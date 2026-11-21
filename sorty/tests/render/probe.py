import bpy, sys, os
print("BLENDER", bpy.app.version_string)
print("ENGINES", [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items])
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for t in ('OPTIX','CUDA','HIP','ONEAPI','NONE'):
        try:
            prefs.compute_device_type = t
            prefs.refresh_devices() if hasattr(prefs,'refresh_devices') else prefs.get_devices()
            print("DEVTYPE", t, [(d.name, d.type, d.use) for d in prefs.devices])
        except Exception as e:
            print("DEVTYPE", t, "ERR", e)
except Exception as e:
    print("CYCLES PREFS ERR", e)
mat = bpy.data.materials.new("m")
try:
    mat.use_nodes = True
except Exception as e:
    print("use_nodes err", e)
nt = mat.node_tree
print("NODES", [n.bl_idname for n in nt.nodes])
p = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
print("PRINCIPLED", [i.name for i in p.inputs])
for idn in ['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeTexNoise','ShaderNodeTexVoronoi','ShaderNodeValToRGB','ShaderNodeBump','ShaderNodeMapping','ShaderNodeTexCoord','ShaderNodeTexImage','ShaderNodeLightPath','ShaderNodeMixShader','ShaderNodeBsdfTransparent','ShaderNodeBsdfGlass','ShaderNodeVolumeAbsorption','ShaderNodeNewGeometry','ShaderNodeMath','ShaderNodeVectorMath','ShaderNodeSeparateXYZ','ShaderNodeTexGradient','ShaderNodeTexWave','ShaderNodeEmission','ShaderNodeLayerWeight','ShaderNodeFresnel','ShaderNodeRGB','ShaderNodeValue','ShaderNodeMapRange','ShaderNodeDisplacement','ShaderNodeTexChecker','ShaderNodeTexBrick','ShaderNodeBsdfDiffuse','ShaderNodeSubsurfaceScattering','ShaderNodeBsdfTranslucent']:
    try:
        n = nt.nodes.new(idn)
        print("OK", idn, "IN", [f"{i.name}:{i.type}" for i in n.inputs], "OUT", [f"{o.name}:{o.type}" for o in n.outputs])
    except Exception as e:
        print("MISSING", idn, e)
sc = bpy.context.scene
print("VIEW", sc.view_settings.view_transform, sc.view_settings.look)
for vt in ['AgX','Filmic','Standard','Khronos PBR Neutral']:
    try:
        sc.view_settings.view_transform = vt; print("VT ok", vt)
    except Exception as e: print("VT err", vt, e)
for lk in ['None','AgX - Medium High Contrast','Medium High Contrast','AgX - Base Contrast','AgX - High Contrast','AgX - Punchy','Punchy']:
    try:
        sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = lk; print("LOOK ok", lk)
    except Exception as e: print("LOOK err", lk)
print("FILEFORMATS", [e.identifier for e in sc.render.image_settings.bl_rna.properties['file_format'].enum_items])
me = bpy.data.meshes.new("x")
print("mesh attrs:", [a for a in ('use_auto_smooth','set_sharp_from_angle','shade_smooth','shade_flat','calc_normals') if hasattr(me,a)])
print("world use_nodes:", hasattr(bpy.data.worlds.new("w"),'use_nodes'))
print("cycles props:", [p for p in ('samples','use_denoising','denoiser','device','use_adaptive_sampling','adaptive_threshold','denoising_use_gpu') if hasattr(sc.cycles,p)])
try:
    print("DENOISERS", [e.identifier for e in sc.cycles.bl_rna.properties['denoiser'].enum_items])
except Exception as e: print("den err", e)
for f in ['arialbd.ttf','ariblk.ttf','impact.ttf','segoeuib.ttf','seguisym.ttf','seguiemj.ttf','BRUSHSCI.TTF','COOPBL.TTF','georgiab.ttf','verdanab.ttf','bahnschrift.ttf','segoeuil.ttf','arial.ttf','comicbd.ttf','trebucbd.ttf','calibrib.ttf','consolab.ttf','framd.ttf','segoepr.ttf','segoeprb.ttf','segoesc.ttf','Candarab.ttf','GOTHICB.TTF','ROCKB.TTF','BAUHS93.TTF']:
    print("FONT", f, os.path.exists(os.path.join(r"C:\Windows\Fonts", f)))
mods = [e.identifier for e in bpy.types.Modifier.bl_rna.properties['type'].enum_items]
print("MODS", mods)
