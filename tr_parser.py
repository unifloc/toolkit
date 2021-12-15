from typing import List

import pandas as pd


def parse_tr(tr_path: str) -> List[dict]:
    """
    Функция для парсинга технологического режима

    :param tr_path: путь к файлику с технологическим режимом
    :return:
    """
    tr = pd.read_excel(tr_path,
                       skiprows=10,
                       header=None
                       )
    tr_data = []
    for _, row in tr.iterrows():
        well_data = {
            "well_name": row[4],
            "field": row[2],
            "d_cas": row[9],
            "d_tub": row[10],
            "d_ch": row[11],
            "h_perf": row[12],
            "ext_h_perf": row[13],
            "al_type": row[14],
            "esp_type": row[15],
            "rate_nom": row[16],
            "head_nom": row[17],
            "freq": row[18],
            "k_sep": row[19],
            "h_tub": row[20],
            "p_wh": row[21],
            "p_fl": row[22],
            "p_res": row[24],
            "p_in": row[27],
            "p_wf": row[28],
            "q_liq": row[30],
            "wct": row[31],
            "rp": row[33],
            "pb": row[35],
            "rsb": row[36],
            "t_res": row[37],
            "muob": row[42],
            "bob": row[45],
            "gamma_oil": row[46],
            "gamma_wat": row[47],
            "ext_h_tub": row[161],
            "regime": row[173],
            "work_type": row[120],
            "pi": row[51]
        }
        tr_data.append(well_data)

    return tr_data
