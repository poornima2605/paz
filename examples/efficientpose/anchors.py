import numpy as np
from paz.backend.anchors import build_strides


def build_translation_anchors(image_shape, branches,
                              num_scales, aspect_ratios):
    """Builds anchor boxes in centre form for given model.
    Anchor boxes a.k.a prior boxes are reference boxes built with
    various scales and aspect ratio centered over every pixel in the
    input image and branch tensors. They can be strided. Anchor boxes
    define regions of image where objects are likely to be found. They
    help object detector to accurately localize and classify objects at
    the same time handling variations in object size and shape.

    # Arguments
        image_shape: List, input image shape.
        branches: List, EfficientNet branch tensors.
        num_scales: Int, number of anchor scales.
        aspect_ratios: List, anchor box aspect ratios.
        scale: Float, anchor box scale.

    # Returns
        anchor_boxes: Array of shape `(num_boxes, 4)`.
    """
    num_scale_aspect = num_scales * len(aspect_ratios)
    args = (image_shape, branches, num_scale_aspect)
    translation_boxes = []
    for branch_arg in range(len(branches)):
        stride = build_strides(branch_arg, *args)
        boxes = make_branch_translation_boxes(
            *stride, branch_arg, branches, num_scale_aspect)
        translation_boxes.append(boxes)
    translation_boxes = np.concatenate(translation_boxes, axis=0)
    return translation_boxes.astype('float32')


def make_branch_translation_boxes(strides_y, strides_x, branch_arg,
                                  branches, num_scale_aspect):
    centers = compute_translation_centers(
        strides_y, strides_x, branch_arg, branches)
    translation_anchors = append_stride_to_centre(
        centers, strides_x, num_scale_aspect)
    return translation_anchors


def compute_translation_centers(strides_y, strides_x, branch_arg, branches):
    feature_H, feature_W = branches[branch_arg].shape[1:3]
    center_x = (np.arange(0, feature_H) + 0.5) * strides_x[0]
    center_y = (np.arange(0, feature_W) + 0.5) * strides_y[0]
    center_x, center_y = np.meshgrid(center_x, center_y)
    center_x_flattened = center_x.reshape(-1, 1)
    center_y_flattened = center_y.reshape(-1, 1)
    centers = np.concatenate((center_x_flattened, center_y_flattened), axis=1)
    return centers


def append_stride_to_centre(centers, strides_x, num_scale_aspect):
    centers = np.repeat(centers, num_scale_aspect, axis=0)
    num_translation_anchors = centers.shape[0]
    stride_array = np.full((num_translation_anchors, 1), strides_x[0])
    translation_anchors = np.concatenate((centers, stride_array), axis=-1)
    return translation_anchors
