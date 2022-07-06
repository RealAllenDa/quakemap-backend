import re

from loguru import logger

from model.pswave import TravelTimeTableModel, PSWaveTimeModel
from sdk import open_file, relpath, verify_none, func_timer


class PSWave:
    """
    PSWave class to parse EEW's expected arrival time, P & S wave.
    """

    def __init__(self):
        self.pswave_list = []
        self._init_pswave()

    @func_timer
    def _init_pswave(self) -> None:
        """
        Initializes PSWave instance.
        """
        handle = open_file(relpath("../assets/pswave/tjma2001"))
        verify_none(handle)
        raw_file = handle.read()
        handle.close()
        try:
            split_file = re.sub(r"\x20+", " ", raw_file)
            split_with_return_file = split_file.split("\n")
            for i in split_with_return_file:
                line = i.split(" ")
                if len(line) != 5:
                    # Either the file is corrupted, or it's not in
                    # our consideration (unused).
                    continue
                self.pswave_list.append(TravelTimeTableModel(
                    p_time=float(line[1]),
                    s_time=float(line[2]),
                    depth=int(line[3]),
                    distance=int(line[4])
                ))
            logger.success("PSWave instance initialized.")
        except Exception:
            logger.exception("Failed to initialize PSWave instance.")

    @func_timer
    def parse_pswave_time(self, depth: int, time_passed: float) -> PSWaveTimeModel:
        """
        Parses the PSWave time.

        :param depth: The depth of the earthquake
        :param time_passed: The elapsed time of the earthquake
        :return: The PSWave time
        """
        logger.debug(f"Parse PSWave time -> depth: {depth}, distance: {time_passed}")
        if depth > 700 or time_passed > 2000:
            logger.warning("Failed to parse PSWave times (Elapsed time too long or earthquake too deep).")
            return PSWaveTimeModel()
        corresponding_earthquake_list = list(filter(lambda d: d.depth == depth, self.pswave_list))
        if len(corresponding_earthquake_list) == 0:
            logger.warning("Failed to parse PSWave times (No depth corresponding).")
            return PSWaveTimeModel()

        # --- S Wave time
        # last corresponding one => s_last, first corresponding one => s_first
        s_last = list(filter(lambda s_p: s_p.s_time <= time_passed, corresponding_earthquake_list))
        s_first = list(filter(lambda s_p: s_p.s_time >= time_passed, corresponding_earthquake_list))
        if (not s_last) or (not s_first):
            logger.warning("Failed to parse S wave time (no time corresponding).")
            s_time = None
        else:
            s_last = s_last[-1]
            s_first = s_first[0]
            # linear interpolation
            s_time = (time_passed - s_last.s_time) / (s_first.s_time - s_last.s_time) * \
                     (s_first.distance - s_last.distance) + s_last.distance
            logger.debug("S wave time parsed.")

        # --- P Wave time
        # last corresponding one => p_last, first corresponding one => p_first
        p_last = list(filter(lambda s_p: s_p.p_time <= time_passed, corresponding_earthquake_list))
        p_first = list(filter(lambda s_p: s_p.p_time >= time_passed, corresponding_earthquake_list))
        if (not p_first) or (not p_last):
            logger.warning("Failed to parse P wave time (no time corresponding).")
            p_time = None
        else:
            p_last = p_last[-1]
            p_first = p_first[0]
            p_time = (time_passed - p_last.p_time) / (p_first.p_time - p_last.p_time) * \
                     (p_first.distance - p_last.distance) + p_last.distance
            logger.debug("P wave time parsed.")
        return PSWaveTimeModel(
            s_time=s_time,
            p_time=p_time
        )
