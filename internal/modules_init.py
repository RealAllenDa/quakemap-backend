import importlib
import importlib.util
import sys
from typing import Callable

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from env import Env
from model.modules import ModulesEnum, ModulesClassEnum
from modules.base_module import BaseModule
from sdk import func_timer, verify_none, verify_not_used

__all__ = ["module_manager"]


class ModuleManager:
    """
    Manages the modules.
    """

    def __init__(self):
        """
        Initializes the module manager.

        Due to the fact that pydantic models cannot be put into a set
         since they're un-hashable,
         the structure of self._modules_list will be:
            set( tuple(),  tuple(),  ...   )
         the structure of tuple:
            ( module_name, module_class_name )
        """
        self._modules_list = set()
        self._loaded_modules = {}
        self._loaded_classes = {}

    def init(self) -> None:
        """
        The real init function, since real init
         should be called after config had been initialized.
        """
        self._init_list()
        self._init_modules()
        self._init_classes()
        self._init_timer()

    @func_timer
    def _init_list(self) -> None:
        """
        Initializes the list of modules need to be initialized.
        """
        for module in Env.config.modules:
            name, enabled = module
            if (name not in ModulesClassEnum.__members__) or \
                    (name not in ModulesEnum.__members__):
                logger.error("Exhaustive handling of ModulesEnum and/or ModulesClassEnum")
                verify_not_used(f"modules' enum: {name}")
            if enabled:  # Enabled
                self._modules_list.add((
                    ModulesEnum[module[0]].value,
                    ModulesClassEnum[module[0]].value,
                ))

    @func_timer
    def _init_modules(self) -> None:
        """
        Initializes the modules.
        """
        for module in self._modules_list:
            name = module[0]
            self._load_module(f"modules.{name}.main")

    @func_timer
    def _init_classes(self) -> None:
        """
        Initializes the base classes of the modules.
        Will only be used during initialization.
        """
        for module in self._modules_list:
            module_name = module[0]
            class_name = module[1]
            self._load_class(module_name, class_name)

    @func_timer
    def _init_timer(self) -> None:
        """
        Initializes the refreshing timer.
        """
        job_stores = {
            "default": MemoryJobStore()
        }
        executors = {
            "default": ThreadPoolExecutor(30)
        }
        job_defaults = {
            "coalesce": False,
            "max_instances": 5
        }
        scheduler = BackgroundScheduler(jobstores=job_stores, executors=executors,
                                        job_defaults=job_defaults)
        if Env.config.modules.p2p_earthquake:
            scheduler.add_job(func=self._module_refresher(self._loaded_classes["p2p_info"]), trigger="interval",
                              seconds=2,
                              id="p2p")
            scheduler.add_job(func=self._module_refresher(
                self._loaded_classes["p2p_info"],
                "refresh_stations"
            ),
                trigger="interval",
                days=1,
                id="station_update")
        if Env.config.modules.shake_level:
            scheduler.add_job(func=self._module_refresher(self._loaded_classes["shake_level"]),
                              trigger="interval",
                              seconds=2,
                              id="shake_level")
        if Env.config.modules.eew:
            scheduler.add_job(func=self._module_refresher(self._loaded_classes["eew_info"]),
                              trigger="interval",
                              seconds=2,
                              id="eew")
        if Env.config.modules.tsunami:
            scheduler.add_job(func=self._module_refresher(self._loaded_classes["tsunami"]), trigger="interval",
                              seconds=4,
                              id="tsunami")
        if Env.config.modules.global_earthquake:
            scheduler.add_job(func=self._module_refresher(self._loaded_classes["global_earthquake"]),
                              trigger="interval",
                              seconds=5,
                              id="global_eq")
        scheduler.start()

    @func_timer
    def reload(self, name: str) -> None:
        """
        Reloads a module. Unused for now.
        :param name: The module of the module
        """
        module = self._loaded_modules.get(name)
        verify_none(module)
        importlib.reload(module)
        # TODO: Reload class
        # TODO: Reload timer
        logger.success(f"Successfully reloaded module {name}.")

    def get_module_info(self, name: str) -> any:
        """
        Gets the module info by getting its 'info' property.
        :param name: The module name
        :return: The info property
        """
        module = self._loaded_classes.get(name)
        if not module:
            return None
        verify_none(hasattr(module, "info"))
        return module.info

    def _load_module(self, name: str) -> None:
        """
        Loads a module.
        :param name: The name of the module
        """
        if name in sys.modules:
            logger.warning(f"Module {name} already in sys.modules.")
        elif (spec := importlib.util.find_spec(name)) is not None:
            logger.debug(f"Loading module {name}.")
            try:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                self._loaded_modules[name] = module
            except Exception:
                logger.exception(f"Failed to load module {name}.")
            logger.success(f"Successfully loaded module {name}.")
        else:
            logger.error(f"Failed to find module {name}.")

    def _load_class(self, module_name: str, name: str) -> None:
        """
        Loads a class.
        :param module_name: The name of the module
        :param name: The name of the modules' class
        """
        module = self._loaded_modules[f"modules.{module_name}.main"]
        # intentionally not use verify_none because we need detailed debugging
        # info to find out why it failed.
        if not hasattr(module, name):
            verify_not_used(f"module {module_name} with class {name}")
        try:
            class_to_load = getattr(module, name)
            self._loaded_classes[module_name] = class_to_load()
        except Exception:
            logger.exception("Failed to find class to load.")
            return

    def _module_refresher(self, module: BaseModule, func_name: str = "get_info") \
            -> Callable[..., None]:
        """
        Refreshes a module using its get_info function.
        :param module: The module to refresh
        """

        def wrapper_refresh():
            if not hasattr(module, func_name):
                verify_not_used(f"module {module}, func {func_name}")
            try:
                getattr(module, func_name)()
            except Exception:
                logger.exception(f"Failed to refresh {module}.")

        return wrapper_refresh


# Why not put this into Env?
# Initialization of the scheduler requires Env.config -> module section,
# so adding this to Env would cause a circular import.
module_manager = ModuleManager()
