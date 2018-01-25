from __future__ import division
import os
import numpy as np
import pandas as pd
import functools
from keras.preprocessing import image
import matplotlib.pyplot as plt
import matplotlib.path as mplpath

from learning2learn.mpl_textures import (Texture, generate_texture,
                                         get_base_image, add_texture)

def rearrange_points(points):
    """
    A function to sort a list of points in clockwise ordering. This
    will help to ensure that our polygon shapes are whole.
    :param points:
    :return:
    """
    center_x = np.mean([elt[0] for elt in points])
    center_y = np.mean([elt[1] for elt in points])

    # function to compare two points
    def less(a, b):
        # preliminary checks
        if a[0] >= center_x and b[0] < center_x:
            return 1
        if a[0] < center_x and b[0] >= center_x:
            return -1
        if a[0] == center_x and b[0] == center_x:
            if a[1] >= center_y or b[1] >= center_y:
                if a[1] > b[1]:
                    return 1
                else:
                    return -1
            else:
                if b[1] > a[1]:
                    return 1
                else:
                    return -1

        # compute the cross product of vectors (center -> a) x (center -> b)
        det = (a[0] - center_x) * (b[1] - center_y) - \
              (b[0] - center_x) * (a[1] - center_y)
        if det < 0:
            return 1
        elif det > 0:
            return -1

        # Points a and b are on the same line from the center.
        # Check which point is closer to the center.
        d1 = (a[0] - center_x) * (a[0] - center_x) + \
             (a[1] - center_y) * (a[1] - center_y)
        d2 = (b[0] - center_x) * (b[0] - center_x) + \
             (b[1] - center_y) * (b[1] - center_y)
        if d1 > d2:
            return 1
        else:
            return -1

    return sorted(points, key=functools.cmp_to_key(less))

def generate_random_shape(x_min, x_max, y_min, y_max, edge_distance):
    """

    :param x_min:
    :param x_max:
    :param y_min:
    :param y_max:
    :param x_offset:
    :param y_offset:
    :return:
    """
    # Sample a number of points for the polygon
    nb_points = np.random.randint(3, 11)
    # 4 'types' of points; determines the edge that the point will be near
    point_types = ['left', 'right', 'top', 'bottom']
    # Cycle through drawing points of different types
    points = []
    for i in range(nb_points):
        if point_types[i % 4] in ['left', 'right']:
            x = np.random.uniform(0, edge_distance)
            y = np.clip(
                np.random.normal(loc=(y_max - y_min) / 2,
                                 scale=(y_max - y_min) / 8),
                y_min,
                y_max
            )
            if point_types[i % 4] == 'right':
                x = x_max - x
        elif point_types[i % 4] in ['top', 'bottom']:
            x = np.clip(
                np.random.normal(loc=(x_max - x_min) / 2,
                                 scale=(x_max - x_min) / 8),
                x_min,
                x_max
            )
            y = np.random.uniform(0, edge_distance)
            if point_types[i % 4] == 'bottom':
                y = y_max - y
        points.append((x, y))
    # Rearrange the points so that they are in the correct order
    points = rearrange_points(points)
    #     # Now center the points by computing the mean distance
    #     # from the center and then subtracting this mean
    #     x_mean = np.mean([p[0] - (x_max-x_min)/2 for p in points])
    #     y_mean = np.mean([p[1] - (y_max-y_min)/2 for p in points])
    #     points = [(p[0]-x_mean, p[1]-y_mean) for p in points]

    return points

# def generate_colors(nb_colors):
#     """
#     Function to generate a set of nb_colors colors. They
#     are generated such that there is sufficient distance
#     between each color vector. This is better than random
#     color sampling.
#     :param nb_colors: (int) the number of colors to generate
#     :return: (Numpy array) the (nb_colors, 3) color matrix
#     """
#     nb_bins = np.round(np.power(nb_colors, 1 / 3)) + 1
#     vals = np.linspace(0, 0.95, int(nb_bins))
#     colors = []
#     for r in vals:
#         for g in vals:
#             for b in vals:
#                 colors.append([r, g, b])
#
#     colors = sorted(colors, key=lambda x: sum(x))
#     colors = colors[-nb_colors:]
#     return np.asarray(colors)

def generate_colors():
    nb_colors = 64
    nb_bins = 4
    vals = np.linspace(0, 0.9, nb_bins)
    colors = np.zeros(shape=(nb_colors, 3))
    i = 0
    for r in vals:
        for g in vals:
            for b in vals:
                colors[i] = np.asarray([r, g, b])
                i += 1

    return colors

def adjust_contrast(img, factor):
    assert factor >= 1.
    img_p = 1. - img
    img_p /= factor
    img_p = 1. - img_p

    return img_p

def compute_area(shape, img_size=200):
    area = 0
    p = mplpath.Path(shape)
    for i in range(img_size):
        for j in range(img_size):
            if p.contains_point((i, j)):
                area += 1

    return area

def shift_image(img, img_size=(200, 200), scale=30):
    # compute shape boundaries
    y_min = min(np.where(img < 1.)[0])
    y_max = max(np.where(img < 1.)[0])
    x_min = min(np.where(img < 1.)[1])
    x_max = max(np.where(img < 1.)[1])
    # randomly select offsets from a uniform R.V. The boundaries
    # are set such that we don't cut off the object.
    #ox = np.random.randint(low=-x_min, high=img_size[0] - x_max)
    #oy = np.random.randint(low=-y_min, high=img_size[1] - y_max)
    ox = np.random.randint(low=max(-scale, -x_min),
                           high=min(scale, img_size[0] - x_max))
    oy = np.random.randint(low=max(-scale, -y_min),
                           high=min(scale, img_size[1] - y_max))
    # shift the image by offsets
    non = lambda s: s if s < 0 else None
    mom = lambda s: max(0, s)
    shift_img = np.ones_like(img, dtype=np.float32)
    shift_img[mom(oy):non(oy), mom(ox):non(ox)] = img[mom(-oy):non(-oy),
                                                  mom(-ox):non(-ox)]

    return shift_img

# def generate_dataset_parameters(nb_categories, image_size=500,
#                                 mpl_textures=False):
#     """
#
#     :param nb_categories:
#     :param image_size:
#     :param mpl_textures:
#     :return:
#     """
#     # Generate shapes, which are sets of points for which polygons will
#     # be generated
#     shapes = [generate_random_shape(0, 500, 0, 500, 100) for _ in
#               range(nb_categories)]
#     # Generate colors, which are 3-D vectors of values between 0-1 (RGB values)
#     colors = generate_colors(nb_categories)
#     if mpl_textures:
#         # using matplotlib custom textures
#         patch_types = [
#                 'ellipse', 'arc', 'arrow', 'circle',
#                 'rectangle', 'wedge', 'pentagon'
#             ]
#         nb_variations = max(int(np.ceil(nb_categories / len(patch_types))), 3)
#         textures = []
#         for patch_type in patch_types:
#             t_list = [generate_texture(patch_type, image_size=image_size)
#                       for _ in range(nb_variations)]
#             textures.extend(t_list)
#         hatch_types = ['/', '-', '+']
#         for hatch_type in hatch_types:
#             textures.append(Texture(hatch_type, gradient=None))
#             textures.append(Texture(hatch_type, gradient='right'))
#             textures.append(Texture(hatch_type, gradient='left'))
#         textures = np.random.choice(textures, nb_categories, replace=False)
#     else:
#         # using pre-designed textures, which are saved as image files in the
#         # 'data' subfolder
#         assert os.path.isdir('../data/textures')
#         files = sorted([file for file in os.listdir('../data/textures') if
#                         file.endswith('tiff')])
#         assert nb_categories <= len(files)
#
#         # return np.random.choice(files, nb_textures, replace=False)
#         textures = files[:nb_categories]
#
#     return shapes, colors, textures

# def generate_image(shape, color, texture, save_file, mpl_textures=False):
#     """
#
#     :param shape:
#     :param color:
#     :param texture:
#     :param save_file:
#     :return:
#     """
#     # Generate the base image and save it to a file
#     if mpl_textures:
#         img = get_base_image(500, 500, color, shape, gradient=texture.gradient)
#     else:
#         img = image.load_img('../data/textures/%s' % texture,
#                              target_size=(500, 500))
#         img = image.img_to_array(img) / 255.
#         # normalize the texture for color consistency. 0.57248
#         # is the average activation for the whole texture dataset.
#         img *= (0.57248/np.mean(img))
#         img = np.minimum(img, 1.)
#     fig = plt.figure(frameon=False)
#     fig.set_size_inches(5, 5)
#     ax = plt.Axes(fig, [0., 0., 1., 1.])
#     ax.set_axis_off()
#     fig.add_axes(ax)
#     if mpl_textures:
#         ax.imshow(img, interpolation='bicubic')
#         add_texture(ax, texture, 500)
#     else:
#         ax.imshow(img*color, interpolation='bicubic')
#     plt.savefig(save_file)
#     plt.close()
#     # Load the base image from file, crop it using mplpath,
#     # and save back to the file
#     img = image.load_img(save_file, target_size=(500, 500))
#     img = image.img_to_array(img)
#     img /= 255.
#     p = mplpath.Path(shape)
#     for i in range(img.shape[0]):
#         for j in range(img.shape[1]):
#             if not p.contains_point((i, j)):
#                 img[j,i,:] = np.array([1.,1.,1.])
#     fig = plt.figure(frameon=False)
#     fig.set_size_inches(5, 5)
#     ax = plt.Axes(fig, [0., 0., 1., 1.])
#     ax.set_axis_off()
#     fig.add_axes(ax)
#     ax.imshow(img)
#     plt.savefig(save_file, bbox_inches='tight')
#     plt.close()

def generate_image(shape, color, texture, target_size=(200, 200),
                   contrast_factor=1.):
    # Generate the base color
    img_color = np.ones(shape=target_size + (3,), dtype=np.float32) * color
    # Generate the base texture
    img_texture = image.load_img(
        '../data/textures/%s' % texture,
        target_size=target_size,
        interpolation='bicubic'
    )
    img_texture = image.img_to_array(img_texture) / 255.
    img_texture = img_texture[:, :, 0]
    img_texture = adjust_contrast(img_texture, contrast_factor)
    # Put it all together
    img = np.ones(shape=target_size + (4,), dtype=np.float32)
    img[:, :, :3] = img_color
    # img[:,:,3] = img_texture
    # Cutout the shape
    p = mplpath.Path(shape)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            if not p.contains_point((i, j)):
                img[j, i, :] = np.ones_like(img[j, i])
    img = shift_image(img, img_size=target_size, scale=20)
    img[:, :, 3] = img_texture

    return img


def generate_image_wrapper(tup):
    return generate_image(tup[0], tup[1], tup[2], tup[3], tup[4])

# def select_subset(df, nb_select):
#     """
#     Helper function for load_image_dataset. If we are subsampling nb_select
#     samples from a particular category, we would like to choose them such that
#     the colors are optimally spaced. This function does so.
#     :param df:
#     :param nb_select:
#     :return:
#     """
#     assert nb_select <= 15, 'only 15 exemplars to select of each category'
#     nb_categories = df.shape[0]
#     # Sort by color values, get the indices
#     ix = df.sort_values(by='color').index
#     if nb_select == len(ix):
#         return ix.tolist()
#     else:
#         step = int(np.ceil(nb_categories / nb_select)) - 1
#         return [ix[i * step] for i in range(nb_select)]

# def load_images(data_folder, target_size=(200, 200), shift=True):
#     # First load the images
#     files = [file for file in os.listdir(data_folder) if file.endswith('png')]
#     files = sorted(files)
#     imgs = np.zeros(shape=(len(files),)+target_size+(3,), dtype=np.float32)
#     for i, file in enumerate(files):
#         img_path = os.path.join(data_folder, file)
#         img = image.load_img(img_path, target_size=target_size,
#                              interpolation='bicubic')
#         img = image.img_to_array(img) / 255.
#         if shift:
#             img = shift_image(img, img_size=target_size)
#         imgs[i] = img
#     # Now load the feature info
#     feature_file = os.path.join(data_folder, 'data.csv')
#     df = pd.read_csv(feature_file, index_col=0)
#
#     return imgs, df
#
# def load_image_dataset(data_folder, nb_categories=None, nb_exemplars=None,
#                        nb_test=5, target_size=(200, 200)):
#     # First load the data
#     imgs, df = load_images(data_folder, target_size)
#     if nb_categories is None:
#         # if these two parameters are 'None' we will not subsample the data.
#         # simply load and return the images.
#         assert nb_exemplars is None
#         return imgs
#     # Collect a subset of the data according to {nb_categories, nb_exemplars}
#     ix = []
#     for cat in range(nb_categories):
#         ix_cat = select_subset(df[df['shape'] == cat], nb_exemplars + nb_test)
#         ix_cat = list(np.random.permutation(ix_cat))
#         ix.extend(ix_cat)
#     imgs = imgs[ix]
#     df = df.iloc[ix]
#
#     return imgs, df['shape'].as_matrix()