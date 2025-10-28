@echo off
cd /d "%~dp0"
echo Running from: %CD%
@REM py ".\pipelineFAMSA.py"      
@REM py ".\pipelineTreePart.py"   
py ".\pipelineMMSEQS.py"     


