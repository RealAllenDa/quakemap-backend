from io import BytesIO

from PIL import Image
from loguru import logger

from schemas.eew import EEWConvertedIntensityEnum
from schemas.intensity2color import IntensityToColorReturnModel, StationIntensityModel, AreaIntensityModel, \
    IntensityToColorIntEnum
from sdk import verify_type, func_timer


class IntensityToColor:
    """
    Intensity2Color class for EEW expected intensity parsing.

    Currently, there are two methods available for parsing:
        1. Matching with json list created in advance
        2. Interpolating with color
    Considering the cons with method 1, for now,
     only method 2 was being implemented.
    """

    def __init__(self):
        logger.success("Intensity2Color instance initialized.")

    @func_timer
    def intensity2color(self, raw_image: bytes) -> IntensityToColorReturnModel:
        """
        Parses the image into expected intensities.

        :param raw_image: The EEW image file
        """
        verify_type(raw_image, bytes)
        logger.debug("Parsing EEW coloring.")

        return_model = IntensityToColorReturnModel()
        image_fp = Image.open(BytesIO(raw_image))
        image = image_fp.convert("HSV").load()

        from env import Env
        area_intensity_max: dict[str, int] = {}
        for i in Env.centroid_instance.earthquake_station_centroid:
            try:
                # noinspection PyUnresolvedReferences
                pixel_color = image[int(i.point.X), int(i.point.Y)]
            except Exception:
                logger.trace(f"Failed to get EEW intensity picture's pixel: {i.point.X}:{i.point.Y}")
                continue
            pixel_intensity = round(self._color_to_position(pixel_color) * 10 - 3, 2)
            if pixel_intensity > 0.5:
                # Intensity bigger than 0.5
                if 0.5 < pixel_intensity < 1.5:
                    parsed_intensity = "1", 1
                elif 1.5 <= pixel_intensity < 2.5:
                    parsed_intensity = "2", 2
                elif 2.5 <= pixel_intensity < 3.5:
                    parsed_intensity = "3", 3
                elif 3.5 <= pixel_intensity < 4.5:
                    parsed_intensity = "4", 4
                elif 4.5 <= pixel_intensity < 5.0:
                    parsed_intensity = "5-", 5
                elif 5.0 <= pixel_intensity < 5.5:
                    parsed_intensity = "5+", 6
                elif 5.5 <= pixel_intensity < 6.0:
                    parsed_intensity = "6-", 7
                elif 6.0 <= pixel_intensity < 6.5:
                    parsed_intensity = "6+", 8
                elif pixel_intensity >= 6.5:
                    parsed_intensity = "7", 9
                else:
                    logger.trace(f"Intensity value outside range: {pixel_color} vs {pixel_intensity}")
                    continue

                # Area
                if i.sub_region_code not in area_intensity_max:
                    # Add new area
                    area_intensity_max[i.sub_region_code] = 0
                if area_intensity_max[i.sub_region_code] < parsed_intensity[1]:
                    area_intensity_max[i.sub_region_code] = parsed_intensity[1]

                # Station
                full_name = i.region + i.name
                return_model.station_intensities[full_name] = StationIntensityModel(
                    name=full_name,
                    area_code=i.region_code,
                    sub_area_code=i.sub_region_code,
                    latitude=i.location.latitude,
                    longitude=i.location.longitude,
                    intensity=parsed_intensity[0],
                    detail_intensity=pixel_intensity,
                    is_area=False
                )
        image_fp.close()
        return_model.area_intensities, return_model.recommend_areas \
            = self._parse_area_intensities(area_intensity_max)
        return return_model

    def _color_to_position(self, color: list[int]) -> float:
        """
        Pixel color in HSV space to intensity space.
        Functions are full of magic numbers calculated in advance, so
         don't change it until you're absolutely sure with what you're doing!

        :param color: The pixel color in HSV space of [0-1, 0-1, 0-1]
        :return: The corresponding location in intensity space
        """
        p = 0
        h = color[0] / 255
        s = color[1] / 255
        v = color[2] / 255

        if v > 0.1 and s > 0.75:

            if h > 0.1476:
                p = 280.31 * pow(h, 6) - 916.05 * pow(h, 5) + 1142.6 * pow(h, 4) - 709.95 * pow(h, 3) \
                    + 234.65 * pow(h, 2) - 40.27 * h + 3.2217

            if 0.1476 >= h > 0.001:
                p = 151.4 * pow(h, 4) - 49.32 * pow(h, 3) + 6.753 * pow(h, 2) - 2.481 * h + 0.9033

            if h <= 0.001:
                p = -0.005171 * pow(v, 2) - 0.3282 * v + 1.2236

        if p < 0:
            p = 0

        return p

    def _parse_area_intensities(self, area_intensity_max: dict[str, int]) -> tuple[
        dict[str, AreaIntensityModel],
        bool
    ]:
        """
        Parses area intensities.
        If one of the areas include intensities that are bigger than 4,
         than we considered it as a strong earthquake and will display areas instead of stations.
        :param area_intensity_max: The maximum intensity within an area
        :return: Area intensities in a dict + Whether to recommend displaying area coloring
        """
        parsed_areas: dict[str, AreaIntensityModel] = {}
        recommend_areas = False

        from env import Env
        for i in area_intensity_max.keys():
            try:
                intensity = EEWConvertedIntensityEnum[
                    IntensityToColorIntEnum(area_intensity_max[i]).name
                ]
                position_model = Env.centroid_instance.area_position_centroid.content.get(i)
                position = position_model.position
                name = position_model.name
                if area_intensity_max[i] >= 4:
                    recommend_areas = True
            except Exception as e:
                logger.trace(f"Parse area {i} failed: {e}.")
                continue
            parsed_areas[name] = AreaIntensityModel(
                name=name,
                intensity=intensity,
                is_area=True,
                latitude=position[0],
                longitude=position[1]
            )
        return parsed_areas, recommend_areas
