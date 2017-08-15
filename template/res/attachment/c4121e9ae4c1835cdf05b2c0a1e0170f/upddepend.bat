@echo off
@echo ----获取SOUI及数据SDK所需的依赖文件----

@set SOUIPATH=%1
@set SDKPATH=%2

@echo ---------------PATH--------------------------------
@echo SOUIPATH=%SOUIPATH%
@echo SDKPATH=%SDKPATH%
@echo ---------------------------------------------------

@if not exist "%SOUIPATH%" goto updsdk

@rem soui tools
@set souitools=uiresbuilder.exe
@FOR %%I IN (%souitools%) DO @xcopy /f /y  "%SOUIPATH%\tools\%%I" "%~dp0depend\soui\tools\"

@rem soui debug lib
@set souidebuglibs=imgdecoder-gdipd.lib imgdecoder-pngd.lib imgdecoder-stbd.lib imgdecoder-wicd.lib pngd.lib render-gdid.lib render-skiad.lib resprovider-zipd.lib skiad.lib souid.lib translatord.lib utilitiesd.lib zlibd.lib
@FOR %%I IN (%souidebuglibs%) DO @xcopy /f /y  "%SOUIPATH%\bin\%%I" "%~dp0depend\soui\lib\debug\"

@rem soui release lib
@set souireleaselibs=imgdecoder-gdip.lib imgdecoder-png.lib imgdecoder-stb.lib imgdecoder-wic.lib png.lib render-gdi.lib render-skia.lib resprovider-zip.lib skia.lib soui.lib translator.lib utilities.lib zlib.lib
@FOR %%I IN (%souireleaselibs%) DO @xcopy /f /y  "%SOUIPATH%\bin\%%I" "%~dp0depend\soui\lib\release\"

@rem soui include files
@xcopy /f /y  "%SOUIPATH%\components\com-cfg.h" "%~dp0depend\soui\include\components\"
@xcopy /e /f /y "%SOUIPATH%\config\*.*" "%~dp0depend\soui\include\config\"
@xcopy /e /f /y "%SOUIPATH%\SOUI\include\*.*" "%~dp0depend\soui\include\soui\"
@xcopy /e /f /y "%SOUIPATH%\utilities\include\*.*" "%~dp0depend\soui\include\utilities\"


:updsdk

@if not exist "%SDKPATH%" goto quit

@rem sdk include files
@xcopy /f /y "%SDKPATH%\packages\framework\include\dwglobal.h" "%~dp0depend\yysdk\include\"

@xcopy /e /f /y "%SDKPATH%\packages\framework\dwbase\*.*" "%~dp0depend\yysdk\dwbase\"
@if exist "%~dp0depend\yysdk\dwbase\debug" @rd /s /q "%~dp0depend\yysdk\dwbase\debug"
@if exist "%~dp0depend\yysdk\dwbase\release" @rd /s /q "%~dp0depend\yysdk\dwbase\release"
@del /f /q "%~dp0depend\yysdk\dwbase\*.*"
@xcopy /e /f /y "%SDKPATH%\packages\framework\include\dwbase\*.*" "%~dp0depend\yysdk\include\dwbase\"
@rem 删掉组件相关文件
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwcomex.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwcommgr_i.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwcomstore_i.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwcominterface_i.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwcominfoimpl.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwcomcreator.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\dwqcomimpl.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\componentsdkversion.h"
@del /f /q "%~dp0depend\yysdk\include\dwbase\yycomclsid.h"
@if exist "%~dp0depend\yysdk\dwbase\commgr" @rd /s /q "%~dp0depend\yysdk\dwbase\commgr"
@xcopy /f /y "%SDKPATH%\bin\debug\dwbase.lib" "%~dp0depend\yysdk\lib\debug\"
@xcopy /f /y "%SDKPATH%\bin\release\dwbase.lib" "%~dp0depend\yysdk\lib\release\"

@xcopy /e /f /y "%SDKPATH%\packages\framework\dwutility\*.*" "%~dp0depend\yysdk\dwutility\"
@if exist "%~dp0depend\yysdk\dwutility\debug" @rd /s /q "%~dp0depend\yysdk\dwutility\debug"
@if exist "%~dp0depend\yysdk\dwutility\release" @rd /s /q "%~dp0depend\yysdk\dwutility\release"
@del /f /q "%~dp0depend\yysdk\dwutility\*.*"
@xcopy /e /f /y "%SDKPATH%\packages\framework\include\dwutility\*.*" "%~dp0depend\yysdk\include\dwutility\"
@xcopy /f /y "%SDKPATH%\bin\debug\dwutility.lib" "%~dp0depend\yysdk\lib\debug\"
@xcopy /f /y "%SDKPATH%\bin\release\dwutility.lib" "%~dp0depend\yysdk\lib\release\"

@xcopy /e /f /y "%SDKPATH%\packages\framework\duifw\*.*" "%~dp0depend\yysdk\duifw\"
@if exist "%~dp0depend\yysdk\duifw\debug" @rd /s /q "%~dp0depend\yysdk\duifw\debug"
@if exist "%~dp0depend\yysdk\duifw\release" @rd /s /q "%~dp0depend\yysdk\duifw\release"
@del /f /q "%~dp0depend\yysdk\duifw\*.*"
@xcopy /e /f /y "%SDKPATH%\packages\framework\include\duifw\*.*" "%~dp0depend\yysdk\include\duifw\"
@xcopy /f /y "%SDKPATH%\bin\debug\duifw.lib" "%~dp0depend\yysdk\lib\debug\"
@xcopy /f /y "%SDKPATH%\bin\release\duifw.lib" "%~dp0depend\yysdk\lib\release\"

@rem获取string相关文件
@xcopy /f /y "%SDKPATH%\packages\framework\include\sysbase\tool\stringparser.h" "%~dp0depend\yysdk\include\"
@xcopy /f /y "%SDKPATH%\packages\framework\include\sysbase\tool\stringizing.h" "%~dp0depend\yysdk\include\"
@xcopy /f /y "%SDKPATH%\packages\framework\include\sysbase\tool\string_helper.h" "%~dp0depend\yysdk\include\"

@xcopy /e /f /y "%SDKPATH%\packages\include\yycore\*.*" "%~dp0depend\yysdk\include\yycore\"

@set sdkbinexts= dll pdb
@rem debug&release dll&pdb
@set sdkbins=yymainframe yycore yycomstore yycommon netio dwutility dwnet dwbase duifw bizcore bizchannel
@for %%I in (%sdkbinexts%) do @for %%J in (%sdkbins%) do @xcopy /f /y "%SDKPATH%\bin\debug\%%J.%%I" "%~dp0bin\debug\"
@for %%I in (%sdkbinexts%) do @for %%J in (%sdkbins%) do @xcopy /f /y "%SDKPATH%\bin\release\%%J.%%I" "%~dp0bin\release\"
@set sdkdebugbins=protocol4_d loginWrapper_d login_d ImProtocol_d
@for %%I in (%sdkbinexts%) do @for %%J in (%sdkdebugbins%) do @xcopy /f /y "%SDKPATH%\bin\debug\%%J.%%I" "%~dp0bin\debug\"
@set sdkreleasebins=protocol4 loginWrapper login ImProtocol
@for %%I in (%sdkbinexts%) do @for %%J in (%sdkreleasebins%) do @xcopy /f /y "%SDKPATH%\bin\release\%%J.%%I" "%~dp0bin\release\"

@rem Qtdll
@set qtbins=QtCore4.dll QtGui4.dll
@FOR %%I IN (%qtbins%) DO @xcopy /f /y "%SDKPATH%\bin\release\%%I" "%~dp0bin\release\"

:quit