import os
import Lugwit_Module as LM
lprint = LM.lprint

def create_folders(base_path):
    """创建项目所需的所有文件夹结构"""
    
    # 资产绑定路径
    rigging_paths = [
        r"H:\xn_1\Rigging\Char\WangLin\approve",  # 绑定\角色\王林\通过文件
        r"H:\xn_1\Rigging\Char\WangLin\work",     # 绑定\角色\王林\工作文件
        r"H:\xn_1\Rigging\Char\WangLin\Hair",     # 绑定\角色\姜浩_日常装\毛发动力学文件
        r"H:\xn_1\Rigging\Prop\TongQiani\approve",  # 绑定\道具\铜钱\通过文件
        r"H:\xn_1\Rigging\Prop\TongQiani\work",     # 绑定\道具\铜钱\工作文件
        r"H:\xn_1\Rigging\Library\wanglin_fazhen\approve",  # 绑定\特效资产\王林_法阵\通过文件
        r"H:\xn_1\Rigging\Library\wanglin_fazhen\work"      # 绑定\特效资产\王林_法阵\工作文件
    ]
    
    # 资产材质路径
    material_paths = [
        r"H:\xn_1\UE_Mesh\Char\WangLin\Tex_4K",  # 材质\角色\王林\贴图文件夹
        r"H:\xn_1\UE_Mesh\Char\WangLin\Material",  # 材质\角色\王林\材质文件
        r"H:\xn_1\UE_Mesh\Prop\TongQiani\Pr_sourceimages",  # 材质\道具\铜钱\贴图文件夹
        r"H:\xn_1\UE_Mesh\Prop\TongQiani\Material",  # 材质\道具\铜钱\材质文件
        r"H:\xn_1\UE_Mesh\Library\wanglin_fazhen\Pr_sourceimages",  # 材质\特效资产\王林_法阵\贴图文件夹
        r"H:\xn_1\UE_Mesh\Library\wanglin_fazhen\Material"  # 材质\特效资产\王林_法阵\材质文件
    ]
    
    # 毛发相关路径
    hair_paths = [
        r"H:\xn_1\Hair\Char\WangLin\approve",  # 毛发资产\角色\王林\通过文件
        r"H:\xn_1\Hair\Char\WangLin\work",     # 毛发资产\角色\王林\工作文件
        r"H:\xn_1\Hair\Hair_tex\3dPaintTextures\YeTu_A_TBP\YeTu",  # 毛发\毛发贴图\毛发笔刷贴图\野兔_A_特别篇\野兔
        r"H:\xn_1\Hair\xgen\collections\YeTu_A_TBP\YeTu_collection",  # 毛发\xgen\描述信息\野兔_A_特别篇\野兔_A_特别篇
        r"H:\xn_1\Hair\Dyn_Assets\TJCSWYCD_TanFan_A_TBP\Dyn_hair"  # 毛发\解算资产\藤家城三五药材店_摊贩_A_TBP\毛发布料整合资产
    ]
    
    # 场景maya文件路径
    scene_paths = [
        r"H:\xn_1\UE_Mesh\Sets\LuShanJiaoXia_X_R_TBP\approve",  # 场景maya文件\麓山脚下_夏_日_TBP\通过文件
        r"H:\xn_1\UE_Mesh\Sets\LuShanJiaoXia_X_R_TBP\work",     # 场景maya文件\麓山脚下_夏_日_TBP\工作文件
        r"H:\xn_1\UE_Mesh\Sets\LuShanJiaoXia_X_R_TBP\check"     # 场景maya文件\麓山脚下_夏_日_TBP\检查文件
    ]
    
    # 创建基础路径列表
    base_paths = rigging_paths + material_paths + hair_paths + scene_paths
    
    # 创建基础文件夹
    for path in base_paths:
        try:
            if not os.path.exists(path):
                os.makedirs(path)
                lprint(f"创建文件夹成功: {path}")
            else:
                lprint(f"文件夹已存在: {path}")
        except Exception as e:
            lprint(f"创建文件夹失败: {path}")
            lprint(f"错误信息: {str(e)}")
    
    # 创建10集10场的文件夹结构
    for ep in range(2001, 2011):  # 2001-2010集
        ep_num = f"EP{ep:04d}"  # 例如：EP2001
        for sc in range(10, 20):  # 0010-0019场
            sc_num = f"SC{sc:04d}"  # 例如：SC0010
            for shot in range(10, 21):  # 0010-0020镜头
                shot_num = f"{ep_num}_{sc_num}_Shot{shot:04d}"  # 例如：EP2001_SC0010_Shot0010
                
                # 动画相关路径
                anim_paths = [
                    fr"H:\xn_1\Animation\{ep_num}\{sc_num}\check",  # 动画\集数\场次\拍屏文件
                    fr"H:\xn_1\Animation\{ep_num}\{sc_num}\work",   # 动画\集数\场次\工作文件
                    fr"H:\xn_1\Animation\{ep_num}\{sc_num}\approve",  # 动画\集数\场次\通过MAYA文件和拍屏
                    fr"H:\xn_1\Layout\{ep_num}\{sc_num}\approve",  # LY\集数\场次\通过MAYA文件和拍屏
                    fr"H:\xn_1\Layout\{ep_num}\{sc_num}\work",     # LY\集数\场次\工作文件
                    fr"H:\xn_1\Animation\{ep_num}\Motion\{sc_num}\{shot_num}"  # 动画\集数\动补\场次\镜头号\动补数据和拍屏
                ]
                
                # 解算相关路径
                sim_paths = [
                    fr"H:\xn_1\Cache\nCloth\{ep_num}\{sc_num}\{shot_num}\check",  # 解算\布料\集数\场次\镜头\提交拍屏、缓存、文件
                    fr"H:\xn_1\Cache\nCloth\{ep_num}\{sc_num}\{shot_num}\work",   # 解算\布料\集数\场次\镜头\工作文件
                    fr"H:\xn_1\Cache\nCloth\{ep_num}\{sc_num}\{shot_num}\approve",  # 解算\布料\集数\场次\镜头\通过文件、缓存、拍屏
                    fr"H:\xn_1\Assemble\{ep_num}\{sc_num}\{shot_num}\nCloth",  # 解算\abc\集数\场次\镜头\布料abc
                    fr"H:\xn_1\Cache\nHair\{ep_num}\{sc_num}\{shot_num}\check",  # 解算\毛发\集数\场次\镜头\提交拍屏、缓存、文件
                    fr"H:\xn_1\Cache\nHair\{ep_num}\{sc_num}\{shot_num}\work",   # 解算\毛发\集数\场次\镜头\工作文件
                    fr"H:\xn_1\Cache\nHair\{ep_num}\{sc_num}\{shot_num}\approve",  # 解算\毛发\集数\场次\镜头\通过文件、缓存、拍屏
                    fr"H:\xn_1\Cache\nHair\{ep_num}\{sc_num}\{shot_num}\nHairAss",  # 解算\毛发\集数\场次\镜头\毛发代理
                    fr"H:\xn_1\Assemble\{ep_num}\{sc_num}\{shot_num}\nHair"  # 解算\abc\集数\场次\镜头\毛发abc
                ]
                
                # 特效路径
                fx_paths = [
                    fr"H:\xn_1\Effects\VFX\{ep_num}\{sc_num}\{shot_num}\check",  # 特效\特效\集数\场次\镜头号\审核文件
                    fr"H:\xn_1\Effects\VFX\{ep_num}\{sc_num}\{shot_num}\work",   # 特效\特效\集数\场次\镜头号\工程文件
                    fr"H:\xn_1\Effects\VFX\{ep_num}\{sc_num}\{shot_num}\approve",  # 特效\特效\集数\场次\镜头号\通过文件
                    fr"H:\xn_1\Effects\VFX\{ep_num}\{sc_num}\{shot_num}\cache",   # 特效\特效\集数\场次\镜头号\缓存文件
                    fr"H:\xn_1\Effects\VFX\{ep_num}\{sc_num}\{shot_num}\image"  # 特效\特效\集数\场次\镜头号\特效序列、nuke工程
                ]
                
                # 灯光路径
                light_paths = [
                    fr"H:\xn_1\Lighting\{ep_num}\{sc_num}\{shot_num}\check",  # 灯光\集数\场次\镜头号\单帧、mov待审
                    fr"H:\xn_1\Lighting\{ep_num}\{sc_num}\{shot_num}\work",   # 灯光\集数\场次\镜头号\灯光工程文件
                    fr"H:\xn_1\Lighting\{ep_num}\{sc_num}\{shot_num}\approve",  # 灯光\集数\场次\镜头号\maya通过文件
                    fr"H:\xn_1\FinalRenderImages\{ep_num}\{sc_num}\{shot_num}\MayaRender"  # 灯光\集数\场次\镜头号\最终灯光渲染序列
                ]
                
                # 合成路径
                comp_paths = [
                    fr"H:\xn_1\Comp\{ep_num}\{sc_num}\{shot_num}\check",  # 合成\集数\场次\镜头号\单帧、mov待审
                    fr"H:\xn_1\Comp\{ep_num}\{sc_num}\{shot_num}\work",   # 合成\集数\场次\镜头号\工程文件
                    fr"H:\xn_1\Comp\{ep_num}\{sc_num}\{shot_num}\approve"  # 合成\集数\场次\镜头号\通过文件
                ]
                
                # 创建所有路径
                all_paths = anim_paths + sim_paths + fx_paths + light_paths + comp_paths
                for path in all_paths:
                    try:
                        if not os.path.exists(path):
                            os.makedirs(path)
                            lprint(f"创建文件夹成功: {path}")
                        else:
                            lprint(f"文件夹已存在: {path}")
                    except Exception as e:
                        lprint(f"创建文件夹失败: {path}")
                        lprint(f"错误信息: {str(e)}")

if __name__ == "__main__":
    # 检查H盘是否存在
    if not os.path.exists("H:\\"):
        lprint("错误: H盘不存在，请确保H盘已经正确映射")
    else:
        create_folders("H:\\")
        lprint("文件夹创建完成！")
