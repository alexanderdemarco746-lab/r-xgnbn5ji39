import bpy, sys, os, math

def p(*a):
    print("PROBE:", *a)
    sys.stdout.flush()

scene = bpy.context.scene
# compositor in 5.x
try:
    tree = bpy.data.node_groups.new("SortyComp", "CompositorNodeTree")
    scene.compositing_node_group = tree
    p("comp tree ok", tree.bl_idname)
    rl = tree.nodes.new("CompositorNodeRLayers")
    gl = tree.nodes.new("CompositorNodeGlare")
    out = tree.nodes.new("NodeGroupOutput")
    p("glare props:", [a for a in dir(gl) if not a.startswith("_") and a not in dir(bpy.types.Node)])
    p("glare inputs:", [(i.name, i.bl_idname, getattr(i, "default_value", None) if i.bl_idname not in ("NodeSocketColor",) else "color") for i in gl.inputs])
    for i in gl.inputs:
        if i.bl_idname == "NodeSocketMenu":
            try:
                p("menu", i.name, "default", i.default_value)
            except Exception as e:
                p("menu err", e)
    p("glare outputs:", [o.name for o in gl.outputs])
    p("rl outputs:", [o.name for o in rl.outputs][:6])
    p("interface attrs:", [a for a in dir(tree.interface) if not a.startswith("_")])
    s = tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    p("out inputs:", [i.name for i in out.inputs])
    for t in ("Bloom", "BLOOM", "Fog Glow", "FOG_GLOW"):
        try:
            gl.inputs["Type"].default_value = t
            p("glare type set ok:", t)
        except Exception as e:
            p("glare type FAIL", t, str(e)[:120])
    try:
        p("glare_type prop:", gl.glare_type)
    except Exception as e:
        p("no glare_type prop")
except Exception as e:
    import traceback; traceback.print_exc()
    p("comp FAIL", e)

# image settings
ims = scene.render.image_settings
try:
    p("media_type:", ims.media_type, [i.identifier for i in ims.bl_rna.properties["media_type"].enum_items])
except Exception as e:
    p("media err", e)
try:
    ims.media_type = "IMAGE"
    ims.file_format = "PNG"
    p("file_format ok", ims.file_format, ims.color_mode, ims.color_depth)
except Exception as e:
    p("ff err", e)

# text alignment enums
cu = bpy.data.curves.new("t", "FONT")
p("align_x:", [i.identifier for i in cu.bl_rna.properties["align_x"].enum_items])
p("align_y:", [i.identifier for i in cu.bl_rna.properties["align_y"].enum_items])
# mesh.shade_smooth signature
me = bpy.data.meshes.new("m")
try:
    me.shade_smooth()
    p("shade_smooth() ok")
except Exception as e:
    p("shade_smooth err", e)
try:
    me.set_sharp_from_angle(angle=0.5)
    p("set_sharp_from_angle ok")
except Exception as e:
    p("set_sharp err", e)
# bmesh ops
import bmesh
bm = bmesh.new()
try:
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=1.0)
    p("uvsphere ok", len(bm.verts))
except Exception as e:
    p("uvsphere err", e)
bm2 = bmesh.new()
try:
    bmesh.ops.create_cone(bm2, cap_ends=True, cap_tris=False, segments=16, radius1=1, radius2=1, depth=2)
    p("cone ok", len(bm2.verts))
except Exception as e:
    p("cone err", e)
# light attrs
li = bpy.data.lights.new("a", "AREA")
p("area light attrs:", [a for a in dir(li) if not a.startswith("_") and a not in dir(bpy.types.ID)][:60])
# world
w = bpy.data.worlds.new("w")
try:
    w.use_nodes = True
except Exception as e:
    p("world use_nodes err", e)
p("world nodes:", [n.bl_idname for n in w.node_tree.nodes] if w.node_tree else None)
# shader node names
mat = bpy.data.materials.new("x")
try:
    mat.use_nodes = True
except Exception as e:
    pass
for nm in ("ShaderNodeEmission", "ShaderNodeBsdfTransparent", "ShaderNodeMixShader", "ShaderNodeTexNoise", "ShaderNodeValToRGB", "ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeBump", "ShaderNodeMixRGB", "ShaderNodeMix", "ShaderNodeTexGradient", "ShaderNodeSeparateXYZ", "ShaderNodeMath", "ShaderNodeLightPath", "ShaderNodeNewGeometry", "ShaderNodeTexVoronoi", "ShaderNodeLayerWeight", "ShaderNodeFresnel", "ShaderNodeBsdfGlass", "ShaderNodeMapRange"):
    try:
        n = mat.node_tree.nodes.new(nm)
        if nm in ("ShaderNodeTexNoise", "ShaderNodeMix", "ShaderNodeMapRange", "ShaderNodeBump", "ShaderNodeTexVoronoi"):
            p(nm, "inputs:", [i.name for i in n.inputs], "outputs:", [o.name for o in n.outputs])
    except Exception as e:
        p("node FAIL", nm, str(e)[:80])
p("cycles object attrs:", [a for a in dir(bpy.types.Object) if "shadow" in a or "caustic" in a][:20])
p("DONE")
