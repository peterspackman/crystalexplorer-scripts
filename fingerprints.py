import sbf
import numpy as np
import matplotlib.pyplot as plt


def histogram(surface_file):
    de, di = read_de_di(surface_file)
    return np.histogram2d(di, de, bins=200, range=((0, 2.5), (0, 2.5)))

def read_de_di(surface_file):
    f = sbf.read_file(surface_file)
    return f['d_e'].data, f['d_i'].data

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('surface_file1',
                        help='CrystalExplorer surface file in .sbf format')
    parser.add_argument('surface_file2',
                        help='CrystalExplorer surface file in .sbf format')
    args = parser.parse_args()

    fig, axes = plt.subplots(3, 1)
    fig.set_size_inches(4, 12)
    H1, xedges, yedges = histogram(args.surface_file1)
    H2, _, _ = histogram(args.surface_file2)
    X, Y = np.meshgrid(xedges, yedges)
    H1[H1 == 0] = np.nan
    H2[H2 == 0] = np.nan
    c = axes[0].pcolormesh(X, Y, H1, cmap='coolwarm')
    axes[0].set_title(args.surface_file1)
    c = axes[1].pcolormesh(X, Y, H2, cmap='coolwarm')
    axes[1].set_title(args.surface_file2)
    c = axes[2].pcolormesh(X, Y, H1-H2, cmap='coolwarm')
    axes[2].set_title('difference')
    for ax in axes:
        ax.set_xlabel(r'$d_i$')
        ax.set_ylabel(r'$d_e$')
    plt.savefig('fingerprint.png', dpi=300, bbox_inches='tight')

if __name__ == '__main__':
    main()
