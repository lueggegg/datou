@echo off

@echo ---------------------------------------------------

@echo 输入编译过的SOUI路径，比如E:\src\soui2\trunk，直接回车跳过
@set SOUI=E:\soui.taobao

@set SDK=

@echo ---------------------------------------------------

@echo ---------------PATH--------------------------------
@echo SOUIPATH="%SOUI%"
@echo SDKPATH="%SDK%"
@echo ---------------------------------------------------

call upddepend.bat "%SOUI%" "%SDK%"