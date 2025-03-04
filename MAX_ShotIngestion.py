import os
import json
import csv
import time
import traceback
from importlib import *
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI
from datetime import date
import Config as Config

reload(Config)

try:
    import maya.standalone as ms

    ms.initialize()
    print('\n')
    print("Autodesk Maya 2018 Initialized......\n")
except Exception as e:
    print("Maya initialization failed with error code {}.".format(e))

import pymel.core as pm


class MAX_ShotIngestion(object):
    def setup(self, shot_name, seqq_path, dontImportShotData, wait_time):
        os.environ['MAX_PATH'] = Config.MAYA_DOLLAR_PATH
        bulid_errors = []
        pb_errors = []
        temp_dir = '{}/Logs'.format(Config.FILES_SAVING_PATH)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        self.processLog = '{}/MAX_Shot_Injection_{}_{}.log'.format(temp_dir, shot_name, date.today())
        print(self.processLog)
        self.shot_name = shot_name
        self.epi = shot_name.split('_')[0]
        self.seq = shot_name.split('_')[1]
        self.shot = shot_name.split('_')[2]
        seq_path = '{}/{}'.format(seqq_path, self.epi)
        self.shot_cam_fbx_path = '{seq_path}/{epi}_{seq}/Shots/{shot_name}'.format(seq_path=seq_path, epi=self.epi,
                                                                                   seq=self.seq, shot_name=shot_name)
        with open(self.processLog, 'a') as opLog:
            opLog.writelines("Shot Number >>> {}\n\n".format(self.shot_name))
            opLog.writelines("shot_cam_fbx_path >>> {}\n\n".format(self.shot_cam_fbx_path))
            try:
                file_name = 'MAX_{}_Blk_v01_x01.ma'.format(shot_name)
                self.bulid_set(file_name)
                self.MAXUECameraFbxImport(seq_path, dontImportShotData)
                time.sleep(int(wait_time))
                pm.saveFile()
            except Exception as code_error:
                pm.saveFile()
                errors = (traceback.format_exc() + "\n" + str(repr(code_error))).replace("'", '"')
                bulid_errors.append(errors)
                opLog.writelines("\t Error>>>  {} \n\n".format(errors))
            if not bulid_errors:
                try:
                    self.make_playblast()
                except Exception as pb_error:
                    pb_errors.append(self.shot_name)
                    opLog.writelines("\t Error>>>  {} \n\n".format(
                        (traceback.format_exc() + "\n" + str(repr(pb_error))).replace("'", '"')))
            log_path = r'{}\Logs'.format(Config.FILES_SAVING_PATH)
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            with open(r'{}/max_ingestion_error_success_data.log'.format(log_path), 'a') as msg:
                if bulid_errors or pb_errors:
                    msg.writelines("\nerror:{}".format(self.shot_name))
                else:
                    msg.writelines("\nsuccess:{}".format(self.shot_name))

        pm.saveFile()
        cmds.quit(f=1, a=1)

    def bulid_set(self, file_name):
        asset_json = '{}/{}_asset_data.json'.format(self.shot_cam_fbx_path, self.shot_name)
        print(asset_json)
        file_path = os.path.join(Config.FILES_SAVING_PATH, self.shot_name)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        pm.saveAs(os.path.join(file_path, file_name))
        with open(asset_json, "r") as reader:
            info_json_data = json.load(reader)
        for set in info_json_data['sets']:
            set_path = '{}/Prod/MAX/00_CG/scenes/Sets/{}/Data/Sections/'.format(Config.MAYA_DOLLAR_PATH, set)
            if not os.path.exists(set_path):
                continue
            for file in os.listdir(set_path):
                if not file.endswith("_GPU.ma"):
                    continue
                cmds.file("{}/{}".format(set_path, file), r=True, type="mayaAscii", gl=True,
                          mergeNamespacesOnClash=False, namespace='', options="v=0")
        pm.saveFile()

    def MAXUECameraFbxImport(self, seq_path, dontImportShotData):
        """
            Process of importing camera fbx
        return: None
        """
        pm.loadPlugin("fbxmaya.mll")
        csv_file = r'{seq_path}/{epi}_conform/{epi}_conform_bake_data.csv'.format(seq_path=seq_path, epi=self.epi)
        book = csv.DictReader(open(csv_file))
        clientFrame = ''
        end_frame = ''
        for row in book:
            shtDictData = {k.strip(): v for (k, v) in row.items()}
            if row['SubscenePath'].endswith(self.shot_name):
                clientFrame = float(shtDictData['SyncOffsetParent1'].rstrip())
                end_frame = float(shtDictData['Duration'].rstrip())

        grpList = ['UE_Cam', 'Shot_Data']
        for eachGrp in grpList:
            if pm.objExists(eachGrp):
                pm.delete(eachGrp)
        pm.group(em=1, n="UE_Cam")
        cam_fbx = '{}_cam.fbx'.format(self.shot_name)
        self.importFbxPath('{}/{}'.format(self.shot_cam_fbx_path, cam_fbx), clientFrame)
        remFilePath = ['{}/{}'.format(self.shot_cam_fbx_path, e) for e in os.listdir(self.shot_cam_fbx_path)
                       if not e.endswith(('.csv', '_cam.fbx', '.csv#', '.json'))]
        self.impRemainingFBXImport(remFilePath, clientFrame, grp='UE_Cam')
        self.CameraSetting()
        self.updatingKeys(clientFrame)
        if dontImportShotData in "False":
            self.shotWiseFBX(self.shot_cam_fbx_path, clientFrame)
        pm.playbackOptions(e=1, ast=1, aet=end_frame)
        pm.playbackOptions(e=1, min=1, max=end_frame)
        self.ue_other_data_visblity_off()

    def importFbxPath(self, file_path, client_frame):
        """
            Process of importing FBX file
        :return:
        """
        print(file_path, client_frame)
        pm.mel.eval('FBXImport -f "{0}"'.format(file_path))
        fbx_namespace = os.path.splitext(os.path.basename(file_path))[0]
        if fbx_namespace.endswith('_cam'):
            new_name = 'FBX_{}_{}_shot_{}_cam'.format(self.epi, self.seq, self.shot)
            pm.rename('FBX*_cam', new_name)
        elif fbx_namespace.endswith('_cam_noka'):
            new_name = 'FBX_{}_{}_shot_{}_cam_noka'.format(self.epi, self.seq, self.shot)
            pm.rename('FBX*_cam_noka', new_name)
            pm.setAttr("{}.scaleX".format(new_name), 1)
            pm.setAttr("{}.scaleY".format(new_name), 1)
            pm.setAttr("{}.scaleZ".format(new_name), 1)
        else:
            try:
                mesh = pm.PyNode(fbx_namespace).listRelatives(ad=True, type='transform')
                if mesh:
                    for each in mesh:
                        if each == 'SkeletalMeshComponent0':
                            pm.setAttr("SkeletalMeshComponent0.sx", lock=False)
                            pm.setAttr("{}|SkeletalMeshComponent0.sx".format(fbx_namespace), 10)
                            pm.setAttr("SkeletalMeshComponent0.sy", lock=False)
                            pm.setAttr("{}|SkeletalMeshComponent0.sy".format(fbx_namespace), 10)
                            pm.setAttr("SkeletalMeshComponent0.sz", lock=False)
                            pm.setAttr("{}|SkeletalMeshComponent0.sz".format(fbx_namespace), 10)
                            for name in pm.PyNode(fbx_namespace).listRelatives(ad=True, type='joint'):
                                pm.select(name, r=1)
                                pm.keyframe(edit=1, option="insert", r=1, timeChange=client_frame)
                                pm.select(cl=1)
                        pm.rename(each, '{}_{}'.format(fbx_namespace.split('_')[0], each))
                else:
                    pm.select(fbx_namespace, r=1)
                    pm.keyframe(edit=1, option="insert", r=1, timeChange=client_frame)
                    pm.select(cl=1)
            except:
                pass

    def impRemainingFBXImport(self, remFilePath, client_frame, grp='UE_Cam'):
        for eachRemFilePath in remFilePath:
            before_importing = set(pm.ls(assemblies=1))
            self.importFbxPath(eachRemFilePath, client_frame)
            after_importing = set(pm.ls(assemblies=1))
            imported_objs = after_importing.difference(before_importing)
            imported_objs = [e.name() for e in imported_objs]
            for eachImpMesh in imported_objs:
                pm.parent(eachImpMesh, grp)

    def CameraSetting(self):
        _sceneName = pm.sceneName()
        _scene = _sceneName.basename().split('_')
        pm.parent("FBX*_cam", "UE_Cam")
        new_name = 'FBX_{}_{}_shot_{}_cam_noka'.format(self.epi, self.seq, self.shot)
        pm.setAttr("{}.scaleX".format(new_name), 1)
        pm.setAttr("{}.scaleY".format(new_name), 1)
        pm.setAttr("{}.scaleZ".format(new_name), 1)

    def updatingKeys(self, client_frame):
        res = pm.PyNode('UE_Cam')
        pm.select(res)

        sFrame = pm.playbackOptions(q=True, ast=True)
        eFrame = pm.playbackOptions(q=True, aet=True)

        for e in res.listRelatives(c=1):
            if 'cam' in e.name():
                pm.select(e, r=1)
                pm.keyframe(edit=1, option="insert", r=1, timeChange=client_frame, time=(sFrame, eFrame))
                pm.select(cl=1)

    def shotWiseFBX(self, camFolder, client_frame):
        pm.group(em=1, n="Shot_Data")

        shotCsvFile = ['{}/{}'.format(camFolder, e) for e in os.listdir(camFolder) if e.endswith(('.csv', '.CSV'))]
        if shotCsvFile:
            shotCsvFile = shotCsvFile[0]
        else:
            return
        book = csv.DictReader(open(shotCsvFile))
        scenePathsList = []
        offSetVal = ''
        for row in book:
            shtDictData = {k.strip(): v for (k, v) in row.items()}
            scenePaths = str(shtDictData['SubscenePath'].strip())
            res = scenePathsList.append(scenePaths) if ',' not in scenePaths else scenePathsList.extend(
                scenePaths.split(','))
            offSetVal = float(shtDictData['SyncOffset'].strip())

        for eachPath in scenePathsList:
            shotCamFolderPath = '{}/{}'.format(camFolder.split('Game')[0], eachPath)
            if os.path.exists(shotCamFolderPath):
                shtFbxList = ['{}/{}'.format(shotCamFolderPath, e) for e in os.listdir(shotCamFolderPath) if
                              e.endswith('.fbx')]
                print("shtFbxList >>>> ", shtFbxList)
                self.impRemainingFBXImport(shtFbxList, client_frame, grp="Shot_Data")

        pm.setAttr("Shot_Data.scaleX", .1)
        pm.setAttr("Shot_Data.scaleY", .1)
        pm.setAttr("Shot_Data.scaleZ", .1)
        res = pm.PyNode('Shot_Data')
        pm.select(res)

        sFrame = pm.playbackOptions(q=True, ast=True)
        eFrame = pm.playbackOptions(q=True, aet=True)

        for e in res.listRelatives(c=1):
            pm.select(e, r=1)
            pm.keyframe(edit=1, option="over", r=1, timeChange=offSetVal, time=(sFrame, eFrame))

            pm.select(cl=1)

    def ue_other_data_visblity_off(self):
        ue_res = pm.PyNode('UE_Cam')
        for fbx_namespace in ue_res.listRelatives(c=1):
            if fbx_namespace.endswith('_cam') or fbx_namespace.endswith('_cam_noka'):
                continue
            try:
                pm.setAttr('{}.visibility'.format(fbx_namespace), 0)
            except:
                pass
        pm.setAttr("UE_Cam.scaleX", .1)
        pm.setAttr("UE_Cam.scaleY", .1)
        pm.setAttr("UE_Cam.scaleZ", .1)

    def make_playblast(self):
        _path = os.path.join(Config.FILES_SAVING_PATH, self.shot_name)
        if not os.path.exists(_path):
            os.makedirs(_path)
        self.pre_playblast_setup()
        playblast_path = pm.playblast(
            widthHeight=(1280, 720),
            format="qt",
            fo=1,
            filename=os.path.join(_path, os.path.basename(pm.sceneName()).replace('.ma', '.mov')),
            sequenceTime=0,
            clearCache=1,
            viewer=0,
            showOrnaments=1,
            offScreen=True,
            fp=4,
            percent=100,
            compression="H.264",
            quality=100)
        return playblast_path

    def pre_playblast_setup(self):
        camera = self.get_shot_camera()
        ModelEditor = self.get_model_panel()
        renderere_name = "vp2Renderer"
        hw_render_globals = pm.PyNode("hardwareRenderingGlobals")
        hw_render_globals.ssaoEnable.set(1)
        hw_render_globals.aoam.set(2)
        hw_render_globals.aora.set(4)
        hw_render_globals.aofr.set(32)
        hw_render_globals.aosm.set(16)
        pm.modelEditor(ModelEditor, e=True, allObjects=False)
        pm.modelEditor(ModelEditor, e=True, polymeshes=True)
        pm.modelEditor(ModelEditor, e=True, particleInstancers=True)
        pm.modelEditor(ModelEditor, e=True, dynamics=True)
        pm.modelEditor(ModelEditor, e=True, pluginObjects=("gpuCacheDisplayFilter", 1))
        pm.modelEditor(
            ModelEditor,
            edit=True,
            displayTextures=True,
            displayAppearance='smoothShaded',
            rendererName=renderere_name,
            activeOnly=False)

        camera.displayGateMask.set(False)
        camera.displaySafeAction.set(True)
        all_files = pm.ls(type="file")
        pm.PyNode("hardwareRenderingGlobals.enableTextureMaxRes").set(1)
        pm.PyNode("hardwareRenderingGlobals.textureMaxResolution").set(256)
        pm.ogs(reloadTextures=True)

    def get_shot_camera(self):
        cmds.lookThru('FBX_{}_{}_shot_{}_cam'.format(self.epi, self.seq, self.shot))
        active_view = OpenMayaUI.M3dView.active3dView()
        camera_dag = OpenMaya.MDagPath()
        active_view.getCamera(camera_dag)
        camera_path = camera_dag.fullPathName()
        pm_camera = pm.PyNode(camera_path)
        return pm_camera

    def get_model_panel(self):
        _panel = pm.playblast(activeEditor=True)
        return _panel.split("|")[-1]


def main(*args):
    print("args >>>>>>>>>>>>>>>> ", args)
    shotName = args[0]
    seq_path = args[1]
    dontImportShotData = args[2]
    wait_time = args[3]
    x = MAX_ShotIngestion()
    x.setup(shotName, seq_path, dontImportShotData, wait_time)
