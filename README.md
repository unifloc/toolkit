# Построение моделей скважин по данным технологического режима с использованием Python Toolkit

Инструкция по установке Pipesim в Anaconda:

- скопировать папочку с пакетами [по ссылке](https://yadi.sk/d/hOVjOuK2oZvvyA) в папку Lib/site-packages с заменой. 
- подгрузить базу насосов - pipesim_2411.sdf через интерфейс pipesim. Options -> Catalog. 
Выбрать from file и указать путь к pipesim_2411.sdf, выбрать опцию Duplicates overwrite и нажать Import
- скачать по ссылке выше json-базу насосов

- от имени администратора выполнить в cmd
```bash
conda install -c conda-forge traits
conda install -c conda-forge isodate
```

*P.S. Настоящая инструкция действительна для Python 3.8 сборки с официального сайта Anaconda и Pipesim 2017.2*