
from skimage import feature, measure, transform, exposure, util
import numpy
from cine_profiler import print_time


class SiftAligner:

    # based on
    # https://stackoverflow.com/questions/62280342/image-alignment-with-orb-and-ransac-in-scikit-image#62332179

    # @print_time
    def __init__(self, reference):

        self.reference = exposure.equalize_adapthist(reference)
        self.reference = reference
        self.de = feature.SIFT(n_octaves=4)

        self.de.detect_and_extract(self.reference)

        self.ref_keypoints = self.de.keypoints
        self.ref_descriptors = self.de.descriptors

    # @print_time
    def align(self, target):
        "Align the target image to the reference image"

        btarget = exposure.equalize_adapthist(target)
        #btarget = target
        self.de.detect_and_extract(btarget)
        keypoints = self.de.keypoints
        descriptors = self.de.descriptors
        matches = feature.match_descriptors(
            self.ref_descriptors,
            descriptors,
            cross_check=True)
        ref_matches = self.ref_keypoints[matches[:, 0]]
        matches = keypoints[matches[:, 1]]
        transform_robust, inliers = measure.ransac(
            (ref_matches, matches),
            transform.EuclideanTransform,
            min_samples=5,
            residual_threshold=0.5,
            max_trials=250
            )
        robust = transform.EuclideanTransform(
            rotation=transform_robust.rotation,
            translation=-numpy.flip(transform_robust.translation)
            )

        warped = transform.warp(target,
                                robust.inverse,
                                order=1,
                                mode="constant",
                                cval=0,
                                clip=True,
                                preserve_range=True
                                )
        return warped.astype(target.dtype)


class OrbAligner:

    # based on
    # https://stackoverflow.com/questions/62280342/image-alignment-with-orb-and-ransac-in-scikit-image#62332179

    # @print_time
    def __init__(self, ref_img: numpy.ndarray):
        align_orb = feature.ORB(n_keypoints=1000, harris_k=0.0005)
        align_orb.detect_and_extract(ref_img)
        self.ref_descriptors = align_orb.descriptors
        self.ref_keypoints = align_orb.keypoints

    # @print_time
    def align(self, target_img: numpy.ndarray):
        align_orb = feature.ORB(n_keypoints=1000, harris_k=0.0005)
        align_orb.detect_and_extract(target_img)
        target_descriptors = align_orb.descriptors
        target_keypoints = align_orb.keypoints
        matches = feature.match_descriptors(
            self.ref_descriptors,
            target_descriptors,
            cross_check=True
            )
        matches_ref = self.ref_keypoints[matches[:, 0]]
        target_matches = target_keypoints[matches[:, 1]]
        transform_robust, inliers = measure.ransac(
            (matches_ref, target_matches),
            transform.EuclideanTransform,
            min_samples=5,
            residual_threshold=0.5,
            max_trials=1000
            )
        new_transform = transform.EuclideanTransform(
            rotation=transform_robust.rotation
            )
        new_transform = transform.EuclideanTransform(
            translation=-numpy.flip(transform_robust.translation)
            )
        image = transform.warp(
            target_img,
            new_transform.inverse,
            order=1,
            mode="constant",
            cval=0,
            clip=True,
            preserve_range=True
            )
        return image.astype(target_img.dtype)


def test_main():
    from skimage.io import imshow
    from matplotlib import pyplot
    from cine import Cine
    import tube2
    import numpy as np
    c = Cine("data2/mothM3_2022-09-19_Cine1.cine")

    vid_med = c.get_video_median()
    m_bounds = tube2.get_tube(vid_med)
    width = m_bounds[1] - m_bounds[0]
    vid_med = tube2.apply_bounds(vid_med, m_bounds)
    print(vid_med.shape)
    aligner = SiftAligner(vid_med)

    for i in range(c.image_count):
        img = c.get_ith_image(i)
        left, right = tube2.get_tube(img)
        right = left + width
        img_res = tube2.apply_bounds(img, (left, right))
        aligned = aligner.align(img_res)
        d = aligned.astype(np.int16) - vid_med.astype(np.int16)
    imshow(d)
    pyplot.show()


if __name__ == '__main__':
    from skimage.io import imshow
    from matplotlib import pyplot
    from cine import Cine
    import tube2
    import numpy as np
    c = Cine("data2/mothM3_2022-09-19_Cine1.cine")

    vid_med = c.get_video_median()
    m_bounds = tube2.get_tube(vid_med)
    width = m_bounds[1] - m_bounds[0]
    vid_med = tube2.apply_bounds(vid_med, m_bounds)
    print(vid_med.shape)
    aligner = SiftAligner(vid_med)

    for i in range(c.image_count):
        img = c.get_ith_image(i)
        left, right = tube2.get_tube(img)
        right = left + width
        img_res = tube2.apply_bounds(img, (left, right))
        aligned = aligner.align(img_res)
        d = aligned.astype(np.int16) - vid_med.astype(np.int16)
