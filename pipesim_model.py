import json
from typing import Tuple, Optional, Any, Dict

import pandas as pd
from sixgill.pipesim import Model
from sixgill.definitions import ModelComponents, Parameters, Constants, Units


def __define_model(model_path: str):
    """
    Создание модели Pipesim

    :param model_path: путь к модели Pipesim
    :return: модель Pipesim
    """
    # Костылек для задания метрической системы,
    # при первом открытии не ставится метрическая
    model = Model.new(model_path, units=Units.METRIC, overwrite=True)
    model.save()
    model.close()

    model = Model.open(model_path, units=Units.METRIC)

    return model


def __get_esp_model_stages(
        esp_db_path: str,
        rate_nom: float,
        head_nom: float
) -> Tuple[int, int]:
    """
    Определение параметров насоса
    :param esp_db_path:  путь к json-БД насосов
    :param rate_nom: номинальная подача
    :param head_nom: номинальный напор
    """
    with open(esp_db_path, encoding="utf8") as f:
        esp_db = json.load(f)

    for key, esp in esp_db.items():
        if rate_nom == esp["rate_nom_sm3day"]:
            esp_id = key
            index_nom_rate = esp["rate_points"].index(int(esp["rate_nom_sm3day"]))
            head_nom_esp = esp["head_points"][index_nom_rate]
            stages = head_nom // head_nom_esp + 1
            break
    else:
        raise Exception("Не найден насос в базе. Нужно доработать функцию по подбору :)")

    return esp_id, stages


def calc_pt_profile(model_path: str,
                    model_name: str,
                    parameters: Optional[dict] = None,
                    p_wh: float = None, q_liq: float = None) -> \
        Tuple[pd.DataFrame, Dict[Any, pd.DataFrame], Dict[Any, pd.DataFrame]]:
    """
    :param q_liq: дебит жидкости, м3/сут
    :param p_wh: буферное давление, атм
    :param model_path: путь к модели pipesim
    :param model_name: название модели / скважины
    :param parameters:параметры расчета pt профиля
    :return:
    """

    if parameters is None:
        parameters = {
            Parameters.PTProfileSimulation.OUTLETPRESSURE: p_wh,
            Parameters.PTProfileSimulation.LIQUIDFLOWRATE: q_liq,
            Parameters.PTProfileSimulation.FLOWRATETYPE: Constants.FlowRateType.LIQUIDFLOWRATE,
            Parameters.PTProfileSimulation.CALCULATEDVARIABLE:
                Constants.CalculatedVariable.INLETPRESSURE
        }

    model = Model.open(model_path, units=Units.METRIC)

    # Запустим расчет PT-профайла
    results = model.tasks.ptprofilesimulation.run(producer=model_name,
                                                  parameters=parameters)

    # system results
    system_results = pd.DataFrame.from_dict(results.system, orient="index")

    # node results
    nodal_results = {}
    for case, node_res in results.node.items():
        nodal_results.update({case: pd.DataFrame.from_dict(node_res, orient="index")})

    # profile results
    profile_results = {}
    for case, profile in results.profile.items():
        profile_results.update({case: pd.DataFrame.from_dict(profile)})

    return system_results, nodal_results, profile_results


def make_pipesim_model(
        well_data: dict,
        model_path: str,
        esp_db_path: str
):
    """
    Функция, создающая модель Pipesim

    :param well_data: словарь с исходными данными
    :param model_path: путь к модели pipesim
    :param esp_db_path: путь к базе насосов
    """
    model = __define_model(model_path)

    # Добавление скважины в модель
    model.add(ModelComponents.WELL, well_data["well_name"],
              parameters={Parameters.Well.DeviationSurvey.SURVEYTYPE: "TwoDimensional",
                          })

    # Добавление НКТ в скважину
    s_wall = 5.5
    roughness = 0.001
    model.add(ModelComponents.TUBING, "Tubing", context=well_data["well_name"],
              parameters={Parameters.Tubing.TOPMEASUREDDEPTH: 0,
                          Parameters.Tubing.LENGTH: well_data["h_tub"],
                          Parameters.Tubing.INNERDIAMETER: well_data["d_tub"] - 2 * s_wall,
                          Parameters.Tubing.ROUGHNESS: roughness,
                          Parameters.Tubing.WALLTHICKNESS: s_wall})

    # Добавление ЭК в скважину
    s_wall = 8.5
    model.add(ModelComponents.CASING, "Casing", context=well_data["well_name"],
              parameters={Parameters.Casing.TOPMEASUREDDEPTH: 0,
                          Parameters.Casing.LENGTH: well_data["h_perf"],
                          Parameters.Casing.INNERDIAMETER: well_data["d_cas"],
                          Parameters.Casing.ROUGHNESS: roughness,
                          Parameters.Casing.WALLTHICKNESS: s_wall})

    # Добавим инклинометрию в скважину
    trajectory = dict()
    incl_tvd = [
        0,
        float(well_data["h_tub"] - well_data["ext_h_tub"]),
        float(well_data["h_perf"] - well_data["ext_h_perf"])
    ]
    incl_md = [
        0,
        float(well_data["h_tub"]),
        float(well_data["h_perf"])
    ]

    trajectory[Parameters.WellTrajectory.TRUEVERTICALDEPTH] = incl_tvd
    trajectory[Parameters.WellTrajectory.MEASUREDDEPTH] = incl_md
    df_trajectory = pd.DataFrame(trajectory)

    model.set_trajectory(
        context=well_data["well_name"],
        value=df_trajectory
    )

    # Добавим модель PVT
    model.add(ModelComponents.BLACKOILFLUID, "Black Oil",
              parameters={
                  Parameters.BlackOilFluid.GOR: well_data["rp"],
                  Parameters.BlackOilFluid.WATERCUT: well_data["wct"],
                  Parameters.BlackOilFluid.USEDEADOILDENSITY: True,
                  Parameters.BlackOilFluid.DEADOILDENSITY: well_data["gamma_oil"] * 1000,
                  Parameters.BlackOilFluid.WATERSPECIFICGRAVITY: well_data["gamma_wat"],
                  Parameters.BlackOilFluid.GASSPECIFICGRAVITY: 0.7,
                  Parameters.BlackOilFluid.SinglePointCalibration.BELOWBBPOFVF_VALUE: well_data[
                      "bob"],
                  Parameters.BlackOilFluid.SinglePointCalibration.BELOWBBPOFVF_PRESSURE:
                      well_data["pb"] * 1.01325,
                  Parameters.BlackOilFluid.SinglePointCalibration.BELOWBBPOFVF_TEMPERATURE:
                      well_data["t_res"],
                  Parameters.BlackOilFluid.SinglePointCalibration.BUBBLEPOINTSATGAS_VALUE:
                      well_data["rsb"],
                  Parameters.BlackOilFluid.SinglePointCalibration.BUBBLEPOINTSATGAS_PRESSURE:
                      well_data["pb"] * 1.01325,
                  Parameters.BlackOilFluid.SinglePointCalibration.BUBBLEPOINTSATGAS_TEMPERATURE:
                      well_data["t_res"],
                  Parameters.BlackOilFluid.SinglePointCalibration.BELOWBBPLIVEOILVISCOSITY_VALUE:
                      well_data["muob"],
                  Parameters.BlackOilFluid.SinglePointCalibration.BELOWBBPLIVEOILVISCOSITY_TEMPERATURE:
                      well_data["t_res"],
                  Parameters.BlackOilFluid.SinglePointCalibration.BELOWBBPLIVEOILVISCOSITY_PRESSURE:
                      well_data["pb"],
                  Parameters.BlackOilFluid.SinglePointCalibration.LIVEOILVISCCORRELATION:
                      "BeggsAndRobinson",
                  Parameters.BlackOilFluid.LIVEOILVISCOSITYCORR: "BeggsAndRobinson",
                  Parameters.BlackOilFluid.SinglePointCalibration.SOLUTIONGAS: "Standing",
              })

    # Добавим заканчивание в скважину
    model.add(ModelComponents.COMPLETION, "Vert Comp 1", context=well_data["well_name"],
              parameters={Parameters.Completion.TOPMEASUREDDEPTH: well_data["h_perf"],
                          Parameters.Completion.FLUIDENTRYTYPE:
                              Constants.CompletionFluidEntry.SINGLEPOINT,
                          Parameters.Completion.GEOMETRYPROFILETYPE: Constants.Orientation.VERTICAL,
                          Parameters.Completion.IPRMODEL: Constants.IPRModels.IPRPIMODEL,
                          Parameters.Completion.RESERVOIRPRESSURE: well_data["p_res"] * 1.01325,
                          Parameters.IPRPIModel.LIQUIDPI: well_data["pi"],
                          Parameters.Completion.RESERVOIRTEMPERATURE: well_data["t_res"],
                          Parameters.Well.ASSOCIATEDBLACKOILFLUID: "Black Oil",
                          Parameters.IPRPIModel.USEVOGELBELOWBUBBLEPOINT: True})

    if well_data["al_type"] == 'ЭЦН':
        esp_id, stages = __get_esp_model_stages(
            esp_db_path,
            well_data["rate_nom"],
            well_data["head_nom"]
        )
        # Добавим насос в скважину
        model.add(ModelComponents.ESP, "Esp", context=well_data["well_name"],
                  parameters={Parameters.ESP.TOPMEASUREDDEPTH: well_data["h_tub"],
                              Parameters.ESP.OPERATINGFREQUENCY: well_data["freq"],
                              Parameters.ESP.MANUFACTURER: "Unifloc",
                              Parameters.ESP.MODEL: str(esp_id),
                              })
        model.set_value(Well=well_data["well_name"],
                        parameter=Parameters.ESP.NUMBERSTAGES,
                        value=stages)
    # Сохраним модель
    model.save()
    model.close()
    return
