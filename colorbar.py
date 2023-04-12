import numpy as np
import colorsys
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib import pyplot as plt


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


def colormap(prop, scheme='d_norm', minval=None, maxval=None):
    vmin = minval if minval else prop.min()
    vmax = maxval if maxval else prop.max()

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


def plot_colorbar(filename, data_range=(-1, 1), scheme="d_norm", ncolors=256, kind="rects"):
    pts = np.linspace(*data_range, ncolors)
    colors = colormap(pts, scheme=scheme, minval=data_range[0], maxval=data_range[1])
    if kind == "rects":
        fig, ax = plt.subplots(figsize=(1, 5))
        for i, color in enumerate(colors):
            rect = plt.Rectangle((0, i/ncolors), 1, 1 / ncolors, color=color)
            ax.add_patch(rect)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylabel(scheme)
    else:
        custom_cmap = LinearSegmentedColormap.from_list("custom", colors, N=ncolors)
        norm = Normalize(vmin=data_range[0], vmax=data_range[1])
        sm = ScalarMappable(cmap=custom_cmap, norm=norm)
        cbar = plt.colorbar(sm)
    plt.savefig(filename, dpi=300, bbox_inches="tight")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('property', default='d_norm',
                        choices=('d_norm', 'd_e', 'd_i', 'curvedness', 'shape_index'),
                        help='Property to color surfaces by')
    parser.add_argument('--property-min', default=-1.0, type=float,
                        help='Minimum property value for coloring')
    parser.add_argument('--property-max', default=1.0, type=float,
                        help='Maximum property value for coloring')
    parser.add_argument('--output', default='colorbar.png',
                        help='Output file')

    args = parser.parse_args()
    plot_colorbar(args.output, data_range=(args.property_min, args.property_max), scheme=args.property)


if __name__ == '__main__':
    main()
