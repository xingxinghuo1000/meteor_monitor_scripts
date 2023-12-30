import cv2
import os
import inner_const

# one rectagle has four points,
# if one point in mask_img, return True
# if none of the point in mask_img, return False
def is_rectangle_masked(rect, i_m, has_mask):
    if has_mask == 0:
        return False
    x, y, w, h = rect
    origin_width = i_m.shape[1]
    origin_height = i_m.shape[0]
    ZOOM = inner_const.MIDDLE_WIDTH/origin_width
    x = int(x/ZOOM)
    y = int(y/ZOOM)
    w = int(w/ZOOM)
    h = int(w/ZOOM)
    p1 = x, y
    p2 = x + w, y
    p3 = x, y + h
    p4 = x + w, y + h
    for p in [p1, p2, p3, p4]:
        x0, y0 = p1
        if x0 >= origin_width:
            logger.info("fix width out of bound, from %d, to %d", x0, origin_width - 1)
            x0 = origin_width - 1
        if y0 >= origin_height:
            logger.info("fix height out of bound, from %d, to %d", y0, origin_height - 1)
            y0 = origin_height - 1
        # one of the 4 points hit mask
        # 0 means black color
        #logger.info("point x0,y0 : %s", (x0, y0))
        #logger.info("im shape : %s", i_m.shape)
        #logger.info("point value in mask: %s", i_m[y0, x0])
        point_in_mask = i_m[y0, x0]
        tmp_v = int(point_in_mask[0]) + int(point_in_mask[1]) + int(point_in_mask[2])
        value = int(tmp_v / 3)
        if value == 0:
            return True
    # all rectangle is out of mask
    return False


def test_rectangle_masked():

    img1 = cv2.imread(os.path.join("test_data", "mask-1280-720.bmp"))
    rect = (10, 10, 20, 20)
    flag1 = is_rectangle_masked(rect, img1, 1)
    assert flag1 == False

    rect = (1260, 700, 10, 10)
    flag1 = is_rectangle_masked(rect, img1, 1)
    assert flag1 == True


