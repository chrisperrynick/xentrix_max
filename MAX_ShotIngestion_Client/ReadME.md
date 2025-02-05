# **MAX_Ingestion**
 
Before execute the script, Please add MAYA_EXE_PATH, MAYA_DOLLAR_PATH and FILES_SAVING_PATH in Config.py file.

    MAYA_EXE_PATH :- Provide maya exe path("C:\Program Files\Autodesk\Maya2018\bin\maya.exe") to run project maya.
    MAYA_DOLLAR_PATH :- Provide dollar path("//bglrstxtx003/storage/projects/max") to set project environ path.
    FILES_SAVING_PATH :- Provide file_saving path("D:\max_client") to save maya and movie files.

After adding all paths, now run "MAX_ShotIngestion_UI.py" by running the below command

    C:\Python39\python.exe <PATH TO MAX_ShotIngestion_UI.py>

It will open the UI and prompts the user to browse for the episode path (Eg: "..\Prod\MAX\00_CG\scenes\Animation\Season_02"). 
Once the path is selected, the right side UI displays an option labeled "Select Episode". 
After choosing an episode, all shot numbers associated with that episode are listed. 
The user can then select the desired shot number and click the Ingest button to proceed or start the process.

If any errors, please refer to the  log files in "FILES_SAVING_PATH" for errors.

### Python Modules USed
* os
* sys
* importlib
* PySide2
* subprocess
* json
* csv
* traceback
* datetime

### MAYA api Modules
* maya.cmds
* pymel.core
* maya.OpenMaya
* maya.OpenMayaUI
