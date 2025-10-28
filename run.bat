@echo off
cd /d "%~dp0"
echo Running from: %CD%
@REM py ".\pipelineFAMSA.py"      || exit /b 1
@REM py ".\pipelineTreePart.py"   || exit /b 1
py ".\pipelineMMSEQS.py"     || exit /b 1


