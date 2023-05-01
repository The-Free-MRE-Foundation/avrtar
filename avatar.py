"""Altspace Avatar Assembler
This Blender Python script generates 3D Altspace Avatar models based on customization values.
It reads customization JSON from stdin, assembles the avatar mesh in Blender, and applies
colorization and blending to textures. Additionally, it sets and applies shape keys for
various face and body shapes.

Optional flags:
    -p or --preview: Generates a preview of the avatar in the same folder as the output FBX.
    -r or --rig: Auto-rigs the avatar and exports as a humanoid rig.
    -c or --vrc: Prepares the model for VRC (forces auto-rigging) and packs textures into an atlas.

Note:
    The shape key feature is only supported on Windows, and some features may not work on Linux.
"""

__author__ = "luminosity_altvr"
__copyleft__ = "Copyleft 2023, The Free MRE Foundation"
__credits__ = ["DaveVR", "maximuszesala", "BenG"]
__license__ = "GPLv3"
__version__ = "0.0.1"
__email__ = "luminosity@freemre.com"
__discord__ = "luminosity#6969"

import bpy
import sys
import os
import re
import json
import logging
import argparse
from enum import Enum
from hashlib import sha256

logging.basicConfig(level=logging.DEBUG)


# global
models = sorted(os.listdir('Models'))
textures = sorted(os.listdir('Textures'))
eyes = sorted(os.listdir('Textures/eyes'))
mouths = sorted(os.listdir('Textures/mouths'))
colors = {}

pi = 3.14159265
tmp_dir = 'tmp'


def isSelected(v):
    return not v.startswith("No_")


def match(filename, value):
    """
    :param filename: string
    :param value: string
    :return: boolean true if a contains b false otherwise
    """
    return \
        value.lower() \
        in \
        filename.replace('.fbx', '')\
        .replace('.png', '')\
        .replace(' ', '_')\
        .lower()


def findModel(v):
    files = models
    # substring match
    matches = list(filter(lambda m: match(m, v), files))
    if len(matches) > 0:
        return matches

    # try removing trailing _001
    v1 = re.sub(r'_00\d', '', v)
    matches = list(filter(lambda m: match(m, v1), files))
    if len(matches) > 0:
        return matches

    # try replacing first word with geo
    v2 = "Geo_"+re.sub(r'^[A-Za-z]+_', '', v)
    matches = list(filter(lambda m: match(m, v2), files))
    if len(matches) > 0:
        return matches

    # try replacing first word with ''
    v3 = re.sub(r'^[A-Za-z]+_', '', v)
    matches = list(filter(lambda m: match(m, v3), files))
    if len(matches) > 0:
        return matches

    return []


def findTexture(v):
    files = textures
    v = v.replace('_HatHair', '')
    # substring match
    matches = list(filter(lambda m: match(m, v), files))
    if len(matches) > 0:
        return matches

    # try removing trailing _001
    v1 = re.sub(r'_00\d', '', v)
    matches = list(filter(lambda m: match(m, v1), files))
    if len(matches) > 0:
        return matches

    # try replace first word with ''
    v2 = re.sub(r'^[A-Za-z]+_', '', v)
    matches = list(filter(lambda m: match(m, v2), files))
    if len(matches) > 0:
        return matches
    return []


def findJacketColor(v):
    keys = colors.keys()
    matches = list(filter(lambda m: match(m, v), keys))
    if len(matches) > 0:
        return matches[0]
    return 'Generic Jacket Secondary Color'


def findPatternName(properties):
    kl = list(filter(
        lambda k: not 'Geo' in k and 'Plain' not in properties[k],
        properties.keys()
    ))
    if len(kl) > 0:
        return properties[kl[0]]


def findPatternTexture(v, patterns):
    # substring match
    matches = list(filter(lambda m: match(m, v), patterns))
    if len(matches) > 0:
        return matches

    # try replacing first word with geo
    v2 = re.sub(r'^Variant_', '', v)
    matches = list(filter(lambda m: match(m, v2), patterns))
    if len(matches) > 0:
        return matches

    # try removing last word
    v3 = re.sub(r'^Variant_', '', v)
    v3 = re.sub(r'_[a-zA-Z]+$', '', v3)

    matches = list(filter(lambda m: match(m, v3), patterns))
    if len(matches) > 0:
        return matches
    return []


def findAndImport(
    v, id,
    p=None,
    mainTexture=None,
    mainColor=(1, 1, 1, 1),
    secondTexture=None,
    secondColor=None,
    shapeKeys=None,
    excludes=[],
    includes=[],
    exact=False
):
    """
    :param v: name of the object to find
    :param id: unique id for this avatar customization
    :param mainTexture: manually specify main texture
    :param mainColor: color to blend the main texure with
    :param secondTexture: manually specify second texture
    :param secondColor: color to blend the second texture with
        (alpha value to blend with main texture) 
    :param excludes: for excluding meshes and textures
    :param includes: for including meshes
    :param exact: mesh must be an exact match not partial match
    """
    if not v:
        return False

    # find mesh
    if not exact:
        modelMatches = findModel(v)
        if len(excludes) > 0:
            modelMatches = list(filter(lambda m: all(
                not e in m for e in excludes), modelMatches))
        if len(includes) > 0:
            modelMatches = list(filter(lambda m: any(
                i in m for i in includes), modelMatches))

        if len(modelMatches) <= 0:
            logging.error("No model matches found for %s" % (v))
            return False

        logging.debug("Found %d model matches for %s: %s" %
                      (len(modelMatches), v, modelMatches if len(modelMatches) > 0 else []))
        m = modelMatches[0]
    else:
        m = "%s.fbx" % (v)
    logging.debug("Selected model %s" % (m))

    # import mesh
    bpy.ops.import_scene.fbx(
        filepath=os.path.abspath(
            os.path.join('Models', m)
        )
    )
    name = m.strip('.fbx')
    object = bpy.context.scene.objects[name]

    # main texture
    if not mainTexture:
        textureMatches = findTexture(v)
        if len(excludes) > 0:
            textureMatches = list(filter(lambda m: all(
                not e in m for e in excludes), textureMatches))
        if len(textureMatches) <= 0:
            textureMatches = ['Body_BaseColor.png']
        logging.debug("Found %d texture matches for %s: %s" %
                      (len(textureMatches), v, textureMatches if len(textureMatches) > 0 else []))
        t = list(filter(lambda m: 'BaseColor' in m, textureMatches))
        t = sorted(t, key=lambda k: len(k))[0]
    else:
        textureMatches = [mainTexture]
        t = textureMatches[0]
    logging.debug("Selected main texture %s" % (t))

    tmp_path = getTmpPath(id)
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    mainTextureFilepath = os.path.abspath(os.path.join('Textures', t))

    # blend filename has the same as the main texture filename
    blendFilename = os.path.basename(mainTextureFilepath)
    blendFilepath = os.path.abspath(os.path.join(tmp_path, blendFilename))

    # if there's a second texture, blend it with maintexture
    secondTextureFilepath = None
    if p:
        logging.debug("Pattern is %s" % (p))
        t2 = list(filter(lambda m: 'PatternColor' in m, textureMatches))
        if secondTexture:
            t2 = secondTexture
        elif len(t2) > 0 and secondColor:
            pt = findPatternTexture(p, t2)
            t2 = t2[-1] if len(pt) <= 0 else pt[-1]
        else:
            t2 = None
            logging.debug("Failed to find a pattern")

        if t2:
            logging.debug("Selected secondary texture %s" % (t2))
            secondTextureFilepath = os.path.abspath(
                os.path.join('Textures', t2)
            )
    blend(
        v,
        mainTextureFilepath=mainTextureFilepath,
        mainColor=mainColor,
        secondTextureFilepath=secondTextureFilepath,
        secondColor=secondColor,
        blendFilepath=blendFilepath
    )

    # create a new material and apply the blend texture
    material = bpy.data.materials.new(v)
    material.use_nodes = True
    bsdf = material.node_tree.nodes["Principled BSDF"]

    texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = bpy.data.images.load(blendFilepath)

    material.node_tree.links.new(
        bsdf.inputs['Base Color'],
        texture.outputs['Color']
    )
    material.node_tree.\
        nodes["Principled BSDF"].\
        inputs['Roughness'].\
        default_value = 1

    object.data.materials.clear()
    object.data.materials.append(material)

    # shape keys
    if object.data.shape_keys and shapeKeys:
        logging.debug(
            "Setting shape key %f, %f, %f" %
            (shapeKeys[0], shapeKeys[1], shapeKeys[2])
        )
        # set value
        i = 0
        kbs = object.data.shape_keys.key_blocks
        for kb in kbs:
            if kb.name == 'Basis':
                continue
            if i >= len(shapeKeys):
                break
            kb.value = shapeKeys[i]
            i += 1
        # apply
        # 1. create new key from mix
        object.shape_key_add(name='Mix Key', from_mix=True)
        ai = kbs.find('Mix Key')
        object.active_shape_key_index = ai
        # 2. in edit mode, vertex => propagate shape to all
        bpy.context.view_layer.objects.active = object
        bpy.ops.object.mode_set(mode='EDIT')
        for v in object.data.vertices:
            v.select = True
        bpy.ops.mesh.shape_propagate_to_all()
        # 3. in object mode clear shape key
        bpy.ops.object.mode_set(mode='OBJECT')
        object.shape_key_clear()

    return True


def findEye(v):
    matches = list(filter(lambda m: match(m, v), eyes))
    if len(matches) > 0:
        return matches
    return []


def setEyes(v, id):
    eyeMatches = findEye(v)
    if len(eyeMatches) <= 0:
        return

    tmp_path = getTmpPath(id)

    # right eye
    overlay(
        mainTextureFilepath=os.path.abspath(
            os.path.join(tmp_path, 'Avatar_Head_BaseColor.png')
        ),
        secondTextureFilepath=os.path.abspath(
            os.path.join('Textures', 'eyes', eyeMatches[0])
        ),
        cutoff=0.001,
        uv=(0.05, 0.21),
        scale=1/4
    )

    # left eye
    overlay(
        mainTextureFilepath=os.path.abspath(
            os.path.join(tmp_path, 'Avatar_Head_BaseColor.png')
        ),
        secondTextureFilepath=os.path.abspath(
            os.path.join('Textures', 'eyes', eyeMatches[0])
        ),
        cutoff=0.001,
        uv=(0.24, 0.21),
        scale=1/4,
        flipX=True
    )


def findMouth(v):
    matches = list(filter(lambda m: match(m, v), mouths))
    if len(matches) > 0:
        return matches
    return []


def setMouth(v, id):
    mouthMatches = findMouth(v)
    if len(mouthMatches) <= 0:
        logging.error("No mouths found.")
        return

    logging.debug("Found mouth %s", mouthMatches[0])
    tmp_path = getTmpPath(id)
    overlay(
        mainTextureFilepath=os.path.abspath(
            os.path.abspath(
                os.path.join(tmp_path, 'Avatar_Head_BaseColor.png')
            )
        ),
        secondTextureFilepath=os.path.abspath(
            os.path.abspath(
                os.path.join('Textures', 'mouths', mouthMatches[0])
            )
        ),
        cutoff=0.001,
        uv=(0.141, 0.06),
        scale=0.28
    )


def findEyeBrow(v):
    matches = list(filter(lambda m: match(m, v), textures))
    if len(matches) > 0:
        return matches
    return []


def setEyeBrows(v, id, mainColor=(1, 1, 1, 1)):
    eyeBrowMatches = findEyeBrow(v)
    if len(eyeBrowMatches) <= 0:
        logging.error("No eye brow found. for %s" % (v))
        return

    logging.debug("Found eye brow %s", eyeBrowMatches[0])
    tmp_path = getTmpPath(id)

    # right eye brow
    overlay(
        mainTextureFilepath=os.path.abspath(
            os.path.join(tmp_path, 'Avatar_Head_BaseColor.png')
        ),
        secondTextureFilepath=os.path.abspath(
            os.path.join('Textures', eyeBrowMatches[0])
        ),
        cutoff=0.001,
        uv=(0.24, 0.265),
        scale=1/4,
        mainColor=mainColor,
        mode=CutoffMode.ALPHA
    )

    # left eye brow
    overlay(
        mainTextureFilepath=os.path.abspath(
            os.path.join(tmp_path, 'Avatar_Head_BaseColor.png')
        ),
        secondTextureFilepath=os.path.abspath(
            os.path.join('Textures', eyeBrowMatches[0])
        ),
        cutoff=0.001,
        uv=(0.05, 0.265),
        scale=1/4,
        flipX=True,
        mainColor=mainColor,
        mode=CutoffMode.ALPHA
    )


def setHairBuzzed(id, secondColor=(1, 1, 1, 1)):
    logging.debug("Setting buzzed hair")
    tmp_path = getTmpPath(id)
    blend(
        None,
        mainTextureFilepath=os.path.abspath(
            os.path.join(
                tmp_path, 'Avatar_Head_BaseColor.png'
            )
        ),
        mainColor=(1, 1, 1, 1),
        secondTextureFilepath=os.path.abspath(
            os.path.join(
                'Textures', 'Hair_Shaved_001_BaseColor.png'
            )
        ),
        secondColor=secondColor,
        blendFilepath=None
    )


def findStubble(v):
    matches = list(filter(lambda m: match(m, v), textures))
    if len(matches) > 0:
        return matches
    return []


def setStubble(v, id, secondColor=(1, 1, 1, 1)):
    stubbleMatches = findStubble(v)
    if len(stubbleMatches) <= 0:
        return
    logging.debug("Setting stubble %s" % (v))
    tmp_path = getTmpPath(id)
    blend(
        None,
        mainTextureFilepath=os.path.abspath(
            os.path.join(
                tmp_path, 'Avatar_Head_BaseColor.png'
            )
        ),
        mainColor=(1, 1, 1, 1),
        secondTextureFilepath=os.path.abspath(
            os.path.join(
                'Textures', stubbleMatches[0]
            )
        ),
        secondColor=secondColor,
        blendFilepath=None
    )

######################
# helper functions
######################


def getTmpPath(id):
    tmp_path = os.path.join(tmp_dir, id, 'textures')
    return tmp_path


def blend(
    v,
    mainTextureFilepath, mainColor,
    secondTextureFilepath, secondColor,
    blendFilepath
):
    """
    Blend color with main texture,
    also if second texture exists, blend with main texture,
    blend method:
        mainTexture * mainColor * alpha + secondTexture * secondColor * (1-alpha)

    :param v: name of the blend texture in blender
    :param mainTextureFilePath
    :param mainColor
    :param secondTextureFilePath
    :param secondColor
    :param blendFilepath: the actual file path to the blend texture on harddrive
    :return: None
    """
    mainTexture = bpy.data.images.load(mainTextureFilepath)
    mainTexturePixels = list(mainTexture.pixels[:])
    for i in range(0, len(mainTexturePixels), 4):
        mainTexturePixels[i] *= mainColor[0]
        mainTexturePixels[i+1] *= mainColor[1]
        mainTexturePixels[i+2] *= mainColor[2]
        mainTexturePixels[i+3] *= mainColor[3]

    if secondColor and secondTextureFilepath:
        secondTexture = bpy.data.images.load(secondTextureFilepath)
        secondTexturePixels = list(secondTexture.pixels[:])
        for i in range(0, len(secondTexturePixels), 4):
            alpha = secondTexturePixels[i+3]
            mainTexturePixels[i] = \
                mainTexturePixels[i] * (1-alpha) + \
                secondTexturePixels[i] * secondColor[0] * alpha
            mainTexturePixels[i+1] = \
                mainTexturePixels[i+1] * (1-alpha) + \
                secondTexturePixels[i+1] * secondColor[1] * alpha
            mainTexturePixels[i+2] = \
                mainTexturePixels[i+2] * (1-alpha) + \
                secondTexturePixels[i+2] * secondColor[2] * alpha
            mainTexturePixels[i+3] = \
                mainTexturePixels[i+3] * (1-alpha) + \
                secondTexturePixels[i+3] * secondColor[3] * alpha

    # if target file not specified, save in main texture file
    if not v or not blendFilepath:
        mainTexture.pixels[:] = mainTexturePixels
        mainTexture.save()
        return

    if blendFilepath and not os.path.exists(blendFilepath):
        blend = bpy.data.images.new(
            v,
            width=mainTexture.size[0],
            height=mainTexture.size[1]
        )
        blend.pixels[:] = mainTexturePixels
        blend.filepath_raw = blendFilepath
        blend.file_format = 'PNG'
        blend.save()


def d2(a, b):
    """
    :param a: vector3
    :param b: vector3
    :return: distance between a and b squared
    """
    return (a[0]-b[0])*(a[0]-b[0]) \
        + (a[1]-b[1])*(a[1]-b[1]) \
        + (a[2]-b[2])*(a[2]-b[2])


class CutoffMode(Enum):
    COMPARE = 1
    ALPHA = 2


def overlay(
    mainTextureFilepath, secondTextureFilepath,
    cutoff, uv, scale, flipX=False,
    mainColor=(1, 1, 1, 1),
    mode=CutoffMode.COMPARE
):
    """
    Bake second texure on top of main texture.
    Useful for adding eyes, mouth

    :param mainTextureFilePath
    :param secondTextureFilePath
    :param cutoff: cutoff value for the second texture
    :param uv: uv coordiate of the overlay
    :param scale: scale of the second texture
    :param flipX: wether the second texture is flipped on the X axis
    :param mainColor: color to blend the second texture with
    :param mode: cutoff mode for the second texture
        if compare then cutoff when distance to first pixel is less than cutoff value
        if alpha then cutoff when alpha is less than cutoff value
    :return: None
    """
    mainTexture = bpy.data.images.load(mainTextureFilepath)
    mainTexturePixels = list(mainTexture.pixels[:])
    w1 = mainTexture.size[0]
    h1 = mainTexture.size[1]

    secondTexture = bpy.data.images.load(secondTextureFilepath)
    secondTexturePixels = list(secondTexture.pixels[:])
    secondTextureFirstPixel = secondTexturePixels[:4]
    w2 = secondTexture.size[0]

    for i in range(0, len(secondTexturePixels), 4):
        pixel = secondTexturePixels[i:i+4]
        if mode == CutoffMode.COMPARE:
            if d2(pixel[:3], secondTextureFirstPixel) < cutoff:
                continue
        elif mode == CutoffMode.ALPHA:
            if pixel[3] < cutoff:
                continue

        x2 = i // 4 % w2
        y2 = i // 4 // w2

        x1 = round(uv[0]*w1 + x2 *
                   scale) if not flipX else round(uv[0]*w1 + (w2-x2) * scale)
        y1 = round(uv[1]*h1 + y2 * scale)
        j = (x1 + y1 * w1) * 4
        mainTexturePixels[j] = pixel[0] * mainColor[0]
        mainTexturePixels[j+1] = pixel[1] * mainColor[1]
        mainTexturePixels[j+2] = pixel[2] * mainColor[2]
        mainTexturePixels[j+3] = pixel[3] * mainColor[3]

    mainTexture.pixels[:] = mainTexturePixels
    mainTexture.save()
    return


def add_point_light(
    name,
    location,
    rotation,
    energy=10,
    color=[1, 1, 1]
):
    light_data = bpy.data.lights.new(name=name+"-data", type='POINT')
    light_data.energy = energy
    light_data.color = color

    light_object = bpy.data.objects.new(name=name, object_data=light_data)

    bpy.context.collection.objects.link(light_object)

    light_object.location = location
    light_object.rotation_euler[0] = rotation[0]*(pi/180.0)
    light_object.rotation_euler[1] = rotation[1]*(pi/180.0)
    light_object.rotation_euler[2] = rotation[2]*(pi/180.0)
    return light_object


def clearData():
    bpy.data.batch_remove(bpy.data.objects)
    bpy.data.batch_remove(bpy.data.meshes)
    bpy.data.batch_remove(bpy.data.materials)
    bpy.data.batch_remove(bpy.data.textures)
    bpy.data.batch_remove(bpy.data.images)
    bpy.data.batch_remove(bpy.data.armatures)


def clearDir(dir):
    for filename in os.listdir(dir):
        filepath = os.path.join(dir, filename)
        if os.path.isfile(filepath):
            os.unlink(filepath)


def clearTmp(id):
    # clean up temp files
    clearDir(getTmpPath(id))
    clearDir(os.path.dirname(getTmpPath(id)))


def get_argv_after_doubledash():
    try:
        idx = sys.argv.index("--")
        return sys.argv[idx+1:]  # the list after '--'
    except ValueError as e:  # '--' not in the list:
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--input',
        nargs='?',
        const='input',
        default='-',
        type=str,
        help='input filepath (default: -)'
    )
    parser.add_argument(
        '-o', '--output',
        nargs='?',
        const='output',
        default='Exports/output.fbx',
        type=str,
        help='output filepath (default: Exports)'
    )
    parser.add_argument(
        '-p', '--preview',
        dest='preview',
        action='store_true',
        help='preview (default: False)'
    )
    parser.add_argument(
        '-t', '--thicc',
        dest='thicc',
        action='store_true',
        help='extra thicc (default: False)'
    )
    parser.add_argument(
        '-r', '--rig',
        dest='rig',
        action='store_true',
        help='autorig (default: False)'
    )
    parser.add_argument(
        '-c', '--vrc',
        dest='vrc',
        action='store_true',
        help='optimize for vrc (default: False)'
    )
    args, unknown = parser.parse_known_args(args=get_argv_after_doubledash())

    input = args.input
    output = args.output
    thicc = args.thicc
    preview = args.preview
    vrc = args.vrc
    rig = args.rig or args.vrc  # if vrc then must rig

    if output == '':
        output = '.'
    if os.path.isdir(output):
        output = os.path.join(output, 'output.fbx')
    output = os.path.abspath(output)

    if input != '-' and not os.path.exists(input):
        parser.error("input file %s doesn't exist" % (input))

    fh = sys.stdin if input == '-' else open(input)
    customizations = json.load(fh)
    id = sha256(json.dumps(customizations).encode('utf-8')).hexdigest()
    colors = customizations['color_palette']
    s = customizations['selections']

    # remove defaults (keep camera in case of preview)
    bpy.data.objects.remove(bpy.data.objects["Cube"])
    bpy.data.objects.remove(bpy.data.objects["Light"])

    blendSets = customizations['blend_sets']
    faceShape = blendSets['FaceShape']
    faceShape = list(
        map(
            lambda x: faceShape[x], [
                'Pointy',
                'Square',
                'Chiseled'
            ]
        )
    )
    bodyShape = blendSets['BodyShape']
    bodyShape = list(
        map(
            lambda x: bodyShape[x],
            [
                'Pear',
                'Triangle',
                'Hourglass'
            ]
        )
    )
    if 'NeckArea' in blendSets:
        neckArea = blendSets['NeckArea']
        neckArea = list(
            map(
                lambda x: neckArea[x],
                [
                    'Neck_Shoulders_Tuck_In',
                    'Neck_Shoulders_High',
                    'Neck_Shoulders_Wide'
                ]
            )
        )
    else:
        neckArea = [0, 0, 0]

    if thicc:
        faceShape = [1, 1, 1]
        bodyShape = [1, 1, 1]
        neckArea = [1, 1, 1]

    # head
    findAndImport(
        'Avatar_Head', id,
        mainColor=colors.get('SkinColor', (1, 1, 1, 1)),
        shapeKeys=faceShape
    )

    hat = s.get('Hat', {}).get('value', 'No_Hat').replace(' ', '_')

    # hat special cases
    if ('BaseballCap_Snapback' in hat and s['Hat']['properties']['GeoVariants_BaseballCap_002'] == 'GeoVariant_Backwards'):
        hat = hat.replace('Snapback', 'Snapback_Backwards')
    if 'Robot_Beanie' in hat:
        hat = 'Hat_Robot_001'
    elif 'Robot_BaseballCap' in hat:
        hat = 'Hat_Robot_002'

    hat_t = None
    if 'Snapback_Backwards' in hat:
        hat_t = 'BaseballCap_Snapback_002_Mat_BaseColor.png'

    hair = s.get('Hair', {}).get('value', 'No_Hair').replace(' ', '_')
    hairPattern = findPatternName(s.get('Hair', {}).get('properties', {}))
    # hair special cases
    hair = hair.replace('Curly_Loose_Long', 'Curl_Loose_long')
    hair_t = None
    if hair == 'MidFade_LowVolume_001':
        hair_t = 'MidFade_HighVolume_001_BaseColor.png'
    hair_t2 = None
    if 'SidePart_Short' in hair:
        hair_t2 = 'SidePart_Mid_Wavy_001_PatternColor1.png'
    
    # hair pattern special cases
    if 'Variant_Bob_002' in hair:
        hair_t2 = 'Bob_001_mat_gradient_PatternColor1.png'

    # hair mesh is cutoff when wearing hats
    if isSelected(hat):
        hatPattern = findPatternName(s.get('Hat', {}).get('properties', {}))
        # hat pattern special cases
        if ('Hat_Robot' in hat):
            hatPattern = 'Robot_001_Plain_PatternColor2'
        findAndImport(
            hat, id,
            p=hatPattern,
            mainTexture=hat_t,
            mainColor=colors['Generic Hat Color'],
            secondColor=colors['Generic Hat Secondary Color'],
            shapeKeys=faceShape
        )
        if isSelected(hair):
            findAndImport(
                hair+"_HatHair", id,
                p=hairPattern,
                mainTexture=hair_t,
                mainColor=colors['Hair Color'],
                secondTexture=hair_t2,
                secondColor=colors['Hair Dye Color'],
                shapeKeys=faceShape
            )
    else:
        if isSelected(hair):
            findAndImport(
                hair, id,
                p=hairPattern,
                mainTexture=hair_t,
                mainColor=colors['Hair Color'],
                secondTexture=hair_t2,
                secondColor=colors['Hair Dye Color'],
                shapeKeys=faceShape
            )

    facialHair = s['Facial Hair']['value'].replace(' ', '_')
    if isSelected(facialHair):
        findAndImport(
            facialHair, id,
            mainColor=colors['Hair Color'],
            shapeKeys=faceShape
        )

    eyewear = s['Eyewear']['value'].replace(' ', '_')
    if isSelected(eyewear):
        findAndImport(eyewear, id, mainColor=colors['Generic Glasses Color'])

    noses = s['Noses']['value'].replace(' ', '_')
    # nose special cases
    if noses == 'Nose_Upturned_001':
        noses = 'Nose_Straight_001'

    findAndImport(noses, id, mainColor=colors['SkinColor'])

    # body
    findAndImport(
        'Avatar_Body', id,
        mainColor=colors['SkinColor'],
        shapeKeys=bodyShape
    )

    # top special cases
    top = s['Top']['value'].replace(' ', '_')
    top = top.replace('Top_Crew_Neck_T-Shirt', 'VNeck_Shirt')
    top = top.replace('V-Neck_Shirt', 'VNeck_Shirt')
    if 'Tshirt_Robot_00' in top:
        top = 'Hoodie_Robot_002'
    top_t1 = None
    if top == 'ButtonUp_Shirt_001':
        top_t1 = 'Shirt_Buttonup_001_BaseColor.png'
    elif top == 'ButtonUp_Shirt_002':
        top_t1 = 'Shirt_Buttonup_002_mat_BaseColor.png'
    topPattern = findPatternName(s.get('Top', {}).get('properties', {}))
    top_t2 = None
    top_c2 = colors['Generic Top Secondary Color'];
    if topPattern == 'Blouse_Tied_001_PolkaDot':
        top_t2 = 'Blouse_Tied_001_Mat_PatternColor1.png'
    elif topPattern == 'Variant_Dress_Wrap_001_Floral':
        top_t2 = 'Dress_Wrap_001_mat_Flower_PatternColor1.png'
    elif topPattern == 'Variant_ButtonUp_Vest_001_Dark':
        top_t2 = 'ButtonUp_Vest_001_Dark_PatternColor2.png'
        top_c2 = (0.1, 0.1, 0.1, 1)
    elif topPattern == 'Variant_ButtonUp_Shirt_002_Dots':
        top_t2 = 'Shirt_Buttonup_002_mat_Dots_PatternColor1.png'


    findAndImport(
        top, id,
        p=topPattern,
        mainTexture=top_t1,
        mainColor=colors['Generic Top Color'],
        secondTexture=top_t2,
        secondColor=top_c2,
        excludes=['Cuff', 'Cuffs'],
        shapeKeys=bodyShape
    )

    jacket = s.get('Jacket', {}).get('value', 'No_Jacket').replace(' ', '_')
    jacketExact = False
    # jacket special cases
    if jacket == 'Biker_Jacket':
        jacket = 'Jacket'
        jacketExact = True
    # jacket pattern special cases
    jacketPattern = findPatternName(s.get('Jacket', {}).get('properties', {}))
    if (jacketPattern == 'Variant_TwoTone'):
        jacketPattern = 'Blazer_Tuxedo_001_PatternColor1'
    jacketColor = findJacketColor(jacket)
    logging.debug("Set Jacket Color %s", jacketColor)

    if isSelected(jacket):
        findAndImport(
            jacket, id,
            p=jacketPattern,
            excludes=['Cuff', 'Cuffs'],
            mainColor=colors[jacketColor],
            secondColor=colors['Generic Jacket Secondary Color'],
            shapeKeys=bodyShape,
            exact=jacketExact
        )

    bottom = s.get('Bottom', {}).get('value', 'No_Bottom')
    if isSelected(bottom):
        findAndImport(
            bottom, id,
            mainColor=colors['Generic Bottoms Color'],
            # shapeKeys=(bodyShape[2], 0, 0),
            # shapeKeys=(bodyShape[2],0,0) if bodyShape[2] == 1 else bodyShape
            shapeKeys=bodyShape
        )

    # hands
    nailPattern = findPatternName(s.get('Fingernails', {}).get('properties', {}))
    findAndImport('Avatar_Hand_L', id, mainColor=colors['SkinColor'])
    findAndImport('Avatar_Hand_R', id, mainColor=colors['SkinColor'])
    findAndImport(
        'Avatar_Nails_L', id,
        mainTexture='Fingernails_BaseColor.png',
        mainColor=colors['NailColor'] if nailPattern else colors['SkinColor']
    )
    findAndImport(
        'Avatar_Nails_R', id,
        mainTexture='Fingernails_BaseColor.png',
        mainColor=colors['NailColor'] if nailPattern else colors['SkinColor']
    )

    # cuffs
    logging.debug("Getting Cuffs")
    foundJacketCuffs = True
    cuff = jacket
    cuff_t = None
    # cuffs special cases
    if jacket == 'Jacket':
        cuff = 'Jacket_Cuffs'
        cuff_t = 'Jacket_Biker_001_BaseColor.png'
    if top == 'Hoodie_Robot_002':
        cuff = top
        cuff_t = 'Hoodie_Robot_002_Plain_BaseColor.png'
    if isSelected(jacket):
        lf = findAndImport(
            cuff, id,
            mainTexture=cuff_t,
            mainColor=colors[jacketColor],
            includes=['Cuffs_L', 'Cuff_L']
        )
        rf = findAndImport(
            cuff, id,
            mainTexture=cuff_t,
            mainColor=colors[jacketColor],
            includes=['Cuffs_R', 'Cuff_R']
        )
        foundJacketCuffs = lf & rf
    if not isSelected(jacket) or not foundJacketCuffs:
        mainTexture = list(filter(
            lambda t: 'BaseColor' in t,
            findTexture(top))
        )
        mainTexture = mainTexture[0] \
            if len(mainTexture) > 0 \
            else 'Tshirt_CrewNeck_001_BaseColor.png'
        findAndImport(
            'Cuff_L', id, exact=True,
            mainTexture=mainTexture,
            mainColor=colors['Generic Top Color']
        )
        findAndImport(
            'Cuff_R', id, exact=True,
            mainTexture=mainTexture,
            mainColor=colors['Generic Top Color']
        )

    # eyes and mouth
    eye = s['Eyes']['value'].replace('Eyes ', '')
    setEyes(eye, id)
    mouth = s['Mouth']['value'].replace(' ', '_')
    setMouth(mouth, id)

    # eye brows
    eyeBrows = s['Eyebrows']['value'].replace(' ', '_')

    # eye brows special cases
    eyeBrows = eyeBrows.replace('_01', '_001')
    eyeBrows = eyeBrows.replace('Angled_001', 'EyeBrow_Angled_001')
    eyeBrows = eyeBrows.replace('Eyebrow_', '')
    eyeBrows = eyeBrows.replace('Arched_Thick', 'ArchBushy')
    eyeBrows = eyeBrows.replace('Arched_Medium', 'ArchHigh')
    eyeBrows = eyeBrows.replace('ThickFlat_001', 'ThickFlat')
    setEyeBrows(
        eyeBrows, id,
        mainColor=colors['Hair Color']
    )

    # hair buzzed
    if hair == 'Hair_Buzzed':
        setHairBuzzed(
            id,
            secondColor=colors['Hair Color']
        )

    # face stubble
    stubble = s['Skin']['properties']['FacialHairVariants']
    stubble = s.get('Skin', {})\
        .get('properties', {})\
        .get('FacialHairVariants', 'No_Stubble')
    if isSelected(stubble):
        stubble = stubble.replace('FacialhairVariant_', '')
        setStubble(
            stubble, id,
            secondColor=colors['Hair Color']
        )

    if preview:
        # camera
        camera = bpy.data.objects["Camera"]
        camera.rotation_mode = 'XYZ'
        camera.rotation_euler[0] = 90*(pi/180.0)
        camera.rotation_euler[1] = 0
        camera.rotation_euler[2] = 0
        camera.location.x = -0.021513
        camera.location.y = -2.7
        camera.location.z = 1.36731

        # lighting
        lightA = add_point_light(
            name='LightA',
            location=[2.52447, -1.751, 1.98358],
            rotation=[37.261, 3.16371, 106.936],
            color=[0.9, 1, 0],
            energy=1000
        )

        lightB = add_point_light(
            name='LightB',
            location=[-3.09032, -0.192501, 1.95869],
            rotation=[37.261, 3.16371, 106.936],
            color=[0, 0.9, 1],
            energy=1000
        )

        bpy.ops.import_scene.fbx(
            filepath=os.path.abspath(
                os.path.join(
                    'Models', 'Preview_Background.fbx'
                )
            )
        )
        name = 'Preview_Background'
        background = bpy.context.scene.objects[name]

        preview_dir = os.path.dirname(output)
        fn = os.path.basename(output)
        fn = re.sub(r'\.fbx$', '', fn)
        fn = re.sub(r'$', '.png', fn)
        preview_filepath = os.path.join(preview_dir, fn)
        filepath = os.path.abspath(preview_filepath)
        bpy.context.scene.render.filepath = filepath
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.resolution_x = 512
        bpy.context.scene.render.resolution_y = 512
        bpy.ops.render.render(use_viewport=True, write_still=True)

        bpy.data.objects.remove(background)
        bpy.data.objects.remove(lightA)
        bpy.data.objects.remove(lightB)

    bpy.data.objects.remove(bpy.data.objects["Camera"])

    if rig:
        rig_filepath = os.path.realpath('rig.blend')
        with bpy.data.libraries.load(rig_filepath) as (data_from, data_to):
            data_to.objects = data_from.objects
        for obj in data_to.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)

        logging.debug("Joining meshes ...")
        # fix neck
        body = bpy.data.objects["Avatar_Body"]
        body.select_set(True)
        head = bpy.data.objects["Avatar_Head"]
        head.select_set(True)
        bpy.context.view_layer.objects.active = head
        bpy.ops.object.join()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles(threshold=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')
        # join the meshes into one
        objects = bpy.data.collections['Collection'].all_objects
        for obj in objects:
            obj.select_set(True)

        limbs = bpy.data.objects["Limbs"]
        limbs_group = limbs.vertex_groups.new(name='Limbs')
        limbs_group.add(
            list(map(lambda v: v.index, limbs.data.vertices)),
            0, 'ADD'
        )

        limbs.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()

        # auto rig using the autorig pro addon
        logging.debug("Auto rigging ...")
        # match to rig
        rig = bpy.data.objects["rig"]
        bpy.context.view_layer.objects.active = rig
        bpy.ops.arp.match_to_rig()

        # bind to rig
        mesh = bpy.data.collections['Collection'].all_objects[0]
        control_rig = bpy.data.objects["char_grp"]
        mesh.select_set(True)
        bpy.ops.arp.bind_to_rig()

        # separate limbs
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.vertex_group_set_active(group='Limbs')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.separate(type='SELECTED')

        # rename objects
        for o in objects:
            if o.name == mesh.name:
                o.name = 'Avatar'
            else:
                o.name = 'Limbs'
                bpy.context.view_layer.objects.active = o

        # set rig type to humanoid
        bpy.context.scene.arp_export_rig_type = 'humanoid'

    # export to fbx
    output_dir = os.path.dirname(output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not rig:
        bpy.ops.export_scene.fbx(
            filepath=output,
            embed_textures=True,
            path_mode='COPY'
        )
    else:
        bpy.ops.arp.fix_rig_export()
        bpy.ops.id.arp_export_fbx_panel('EXEC_DEFAULT', filepath=output)

    if vrc:
        clearData()
        bpy.ops.import_scene.fbx(filepath=output)

        # combine materials using the material-combiner-addon
        cwd = os.getcwd()
        dir = os.path.abspath(os.path.join(tmp_dir, id))
        os.chdir(dir)
        bpy.ops.file.unpack_all(method='USE_LOCAL')
        bpy.ops.smc.refresh_ob_data()
        bpy.ops.smc.combiner(cats=False, directory=dir)

        # overwrite
        bpy.ops.export_scene.fbx(
            filepath=output,
            embed_textures=True,
            path_mode='COPY'
        )
        os.chdir(cwd)

    # clean up temp files
    # clearTmp(id)

    logging.debug("Success")
