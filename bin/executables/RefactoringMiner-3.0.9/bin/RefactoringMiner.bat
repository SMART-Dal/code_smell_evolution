@rem
@rem Copyright 2015 the original author or authors.
@rem
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem      https://www.apache.org/licenses/LICENSE-2.0
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.
@rem

@if "%DEBUG%" == "" @echo off
@rem ##########################################################################
@rem
@rem  RefactoringMiner startup script for Windows
@rem
@rem ##########################################################################

@rem Set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" setlocal

set DIRNAME=%~dp0
if "%DIRNAME%" == "" set DIRNAME=.
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%..

@rem Resolve any "." and ".." in APP_HOME to make it shorter.
for %%i in ("%APP_HOME%") do set APP_HOME=%%~fi

@rem Add default JVM options here. You can also use JAVA_OPTS and REFACTORING_MINER_OPTS to pass JVM options to this script.
set DEFAULT_JVM_OPTS=

@rem Find java.exe
if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if "%ERRORLEVEL%" == "0" goto execute

echo.
echo ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
echo.
echo Please set the JAVA_HOME variable in your environment to match the
echo location of your Java installation.

goto fail

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto execute

echo.
echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
echo.
echo Please set the JAVA_HOME variable in your environment to match the
echo location of your Java installation.

goto fail

:execute
@rem Setup the command line

set CLASSPATH=%APP_HOME%\lib\RefactoringMiner-3.0.9.jar;%APP_HOME%\lib\org.eclipse.jgit-6.10.0.202406032230-r.jar;%APP_HOME%\lib\slf4j-simple-2.0.16.jar;%APP_HOME%\lib\spark-core-2.9.4.jar;%APP_HOME%\lib\slf4j-api-2.0.16.jar;%APP_HOME%\lib\gen.jdt-3.0.0.jar;%APP_HOME%\lib\org.eclipse.jdt.core-3.38.0.jar;%APP_HOME%\lib\commons-text-1.12.0.jar;%APP_HOME%\lib\github-api-1.135.jar;%APP_HOME%\lib\java-diff-utils-4.12.jar;%APP_HOME%\lib\core-3.0.0.jar;%APP_HOME%\lib\jcommander-1.83.jar;%APP_HOME%\lib\jsoup-1.18.1.jar;%APP_HOME%\lib\fastutil-8.5.14.jar;%APP_HOME%\lib\rendersnake-1.9.0.jar;%APP_HOME%\lib\JavaEWAH-1.2.3.jar;%APP_HOME%\lib\simmetrics-core-3.2.3.jar;%APP_HOME%\lib\commons-codec-1.17.0.jar;%APP_HOME%\lib\org.eclipse.core.resources-3.20.200.jar;%APP_HOME%\lib\org.eclipse.core.filesystem-1.10.400.jar;%APP_HOME%\lib\org.eclipse.text-3.14.100.jar;%APP_HOME%\lib\org.eclipse.core.expressions-3.9.400.jar;%APP_HOME%\lib\org.eclipse.core.runtime-3.31.100.jar;%APP_HOME%\lib\ecj-3.38.0.jar;%APP_HOME%\lib\commons-lang3-3.14.0.jar;%APP_HOME%\lib\jackson-annotations-2.13.0.jar;%APP_HOME%\lib\jackson-core-2.13.0.jar;%APP_HOME%\lib\jackson-databind-2.13.0.jar;%APP_HOME%\lib\commons-io-2.8.0.jar;%APP_HOME%\lib\classindex-3.10.jar;%APP_HOME%\lib\gson-2.8.2.jar;%APP_HOME%\lib\jgrapht-core-1.5.1.jar;%APP_HOME%\lib\jetty-webapp-9.4.48.v20220622.jar;%APP_HOME%\lib\websocket-server-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-servlet-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-security-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-server-9.4.48.v20220622.jar;%APP_HOME%\lib\websocket-servlet-9.4.48.v20220622.jar;%APP_HOME%\lib\junit-4.8.2.jar;%APP_HOME%\lib\spring-webmvc-4.1.6.RELEASE.jar;%APP_HOME%\lib\jtidy-r938.jar;%APP_HOME%\lib\guice-3.0.jar;%APP_HOME%\lib\javax.inject-1.jar;%APP_HOME%\lib\org.eclipse.core.jobs-3.15.300.jar;%APP_HOME%\lib\org.eclipse.core.contenttype-3.9.400.jar;%APP_HOME%\lib\org.eclipse.equinox.app-1.7.100.jar;%APP_HOME%\lib\org.eclipse.equinox.registry-3.12.100.jar;%APP_HOME%\lib\org.eclipse.equinox.preferences-3.11.100.jar;%APP_HOME%\lib\org.eclipse.core.commands-3.12.100.jar;%APP_HOME%\lib\org.eclipse.equinox.common-3.19.100.jar;%APP_HOME%\lib\org.eclipse.osgi-3.20.0.jar;%APP_HOME%\lib\guava-18.0.jar;%APP_HOME%\lib\jheaps-0.13.jar;%APP_HOME%\lib\javax.servlet-api-3.1.0.jar;%APP_HOME%\lib\websocket-client-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-client-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-http-9.4.48.v20220622.jar;%APP_HOME%\lib\websocket-common-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-io-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-xml-9.4.48.v20220622.jar;%APP_HOME%\lib\websocket-api-9.4.48.v20220622.jar;%APP_HOME%\lib\spring-web-4.1.6.RELEASE.jar;%APP_HOME%\lib\spring-context-4.1.6.RELEASE.jar;%APP_HOME%\lib\spring-aop-4.1.6.RELEASE.jar;%APP_HOME%\lib\spring-beans-4.1.6.RELEASE.jar;%APP_HOME%\lib\spring-expression-4.1.6.RELEASE.jar;%APP_HOME%\lib\spring-core-4.1.6.RELEASE.jar;%APP_HOME%\lib\aopalliance-1.0.jar;%APP_HOME%\lib\cglib-2.2.1-v20090111.jar;%APP_HOME%\lib\org.osgi.service.prefs-1.1.2.jar;%APP_HOME%\lib\jetty-util-ajax-9.4.48.v20220622.jar;%APP_HOME%\lib\jetty-util-9.4.48.v20220622.jar;%APP_HOME%\lib\commons-logging-1.2.jar;%APP_HOME%\lib\asm-3.1.jar;%APP_HOME%\lib\osgi.annotation-8.0.1.jar


@rem Execute RefactoringMiner
"%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %REFACTORING_MINER_OPTS%  -classpath "%CLASSPATH%" org.refactoringminer.RefactoringMiner %*

:end
@rem End local scope for the variables with windows NT shell
if "%ERRORLEVEL%"=="0" goto mainEnd

:fail
rem Set variable REFACTORING_MINER_EXIT_CONSOLE if you need the _script_ return code instead of
rem the _cmd.exe /c_ return code!
if  not "" == "%REFACTORING_MINER_EXIT_CONSOLE%" exit 1
exit /b 1

:mainEnd
if "%OS%"=="Windows_NT" endlocal

:omega
