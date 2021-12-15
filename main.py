import os
from typing import Optional, Tuple, Dict, Any

import pandas as pd

from tr_parser import parse_tr
from pipesim_model import make_pipesim_model, calc_pt_profile


def calc_pt(model_path: str,
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
    :return: system_results, nodal_results, profile_results
    """

    return calc_pt_profile(model_path, model_name, parameters, p_wh, q_liq)


def make_models(tr_path: str, model_directory: str, esp_db_path: str,
                number_of_wells: Optional[int] = None):
    """
    :param tr_path: путь к технологическому режиму
    :param model_directory: путь к директории, где создаются модели
    :param esp_db_path: путь к базе насосов, для выставления корректного насоса в pipesim
    :param number_of_wells: количество скважин для создания моделей, если None то создадутся все
    :return:
    """

    initial_data = parse_tr(tr_path)

    if number_of_wells is not None:
        initial_data = initial_data[: number_of_wells]

    if not os.path.exists(model_directory):
        os.mkdir(model_directory)

    for well_data in initial_data:
        print(f"Создадим модель для скважины: {well_data['well_name']}")
        model_path = model_directory + "/" + well_data["well_name"] + ".pips"

        make_pipesim_model(well_data, model_path, esp_db_path)


if __name__ == "__main__":
    make_models(tr_path="data/Техрежим, Муравленко, декабрь 2021_Действующие_Суторминское.xls",
                model_directory="data/модели pipesim",
                esp_db_path="esp_db.json",
                number_of_wells=2)
