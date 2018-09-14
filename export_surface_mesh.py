import sbf
import trimesh
import numpy as np
import colorsys


RWB = np.array([[0.0, 0.0, 1.0], [1.0, 1.0, 1.0], [1.0, 0.0, 0.0]])
RGB = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])

COLORS = {
    'd_norm': RWB,
    'd_i': RGB,
    'd_e': RGB,
    'curvedness': RGB,
    'shape_index': RGB,
    'deformation_density': RWB,
    'electron_density': RWB,
    'promolecule_density': RWB,
    'electric_potential': RWB,
    'orbital': RWB,
}

def clamp(v, vmin, vmax):
    return max(min(v, vmax), vmin)

def hmap(value, vmin, vmax, reverse, hmin, hmax):
    newval = clamp(value, vmin, vmax)

    range_ratio = 0.0
    r = vmax - vmin
    if r > 1e-6:
        range_ratio = (hmax - hmin) / r

    if reverse:
        h = 1.0 - range_ratio * (newval - vmin)
    else:
        h = range_ratio * (newval - vmin)

    return colorsys.hsv_to_rgb(clamp(h, hmin, hmax), 1.0, 1.0)

def cmap(value, vmin, vmax, start, mid, end):
    if value < 0:
        factor = 1.0 - value / vmin
        color = start
    else:
        factor = 1.0 - value / vmax
        color = end
    res = color + (mid - color) * factor
    return res


def colormap(prop, scheme='d_norm'):
    vmin = prop.min()
    vmax = prop.max()

    colors = np.zeros((prop.shape[0], 3), dtype=np.float32)

    if scheme in {'d_norm', 'electric_potential', 'orbital',
            'deformation_density', 'electron_density'}: 
        start = COLORS[scheme][0,:]
        mid = COLORS[scheme][1,:]
        end = COLORS[scheme][2,:]
        for i, value in enumerate(prop):
            colors[i,:] = cmap(value, vmin, vmax, start, mid, end)
    else:
        hmax = 240.0/359.0
        hmin = 0.0
        for i, value in enumerate(prop):
            colors[i,:] = hmap(value, vmin, vmax, False, hmin, hmax)
    return colors


def get_mesh(verts, faces, normals, colors):
    surface = trimesh.Trimesh(vertices=verts, faces=faces,
                              vertex_normals=normals, vertex_colors=colors)
    return surface


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('surface_files', nargs='+',
                        help='CrystalExplorer surface files in .sbf format')
    parser.add_argument('--property', default='d_norm',
                        choices=('d_norm', 'd_e', 'd_i', 'curvedness', 'shape_index'),
                        help='Property to color surfaces by')
    parser.add_argument('--output-format', default='obj',
                        choices=trimesh.io.export._mesh_exporters.keys(),
                        help='Output file format')

    args = parser.parse_args()
    for filename in args.surface_files:
        f = sbf.read_file(filename)
        prop = f[args.property].data
        name = '.'.join(filename.split('.')[:-1])
        output = '{}.{}'.format(name, args.output_format)
        print("Exporting {} using surface property '{}'".format(
              output, args.property))
        colors = colormap(prop, scheme=args.property)
        vertices = f['vertices'].data.transpose()
        faces = f['faces'].data.transpose() - 1
        normals = f['vertex normals'].data.transpose()
        mesh = get_mesh(vertices, faces, normals, colors)
        mesh.export(output)




if __name__ == '__main__':
    main()
