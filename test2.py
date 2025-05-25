import pyautogui
import time
import random
import logging
from PIL import Image
import cv2
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ColorAutoFight:
    def __init__(self):
        self.min_delay = 0.5
        self.max_delay = 1.5
        self.max_card_change = 3
        self.step_wait = 1.5
        self.screenshot_path = "screenshot.png"

        # 模板路径配置（彩色图）
        self.templates = {
            "start_challenge": "templates/start_challenge.png",
            "cancel": "templates/cancel.png",
            "confirm": "templates/confirm.png",
            "li_jue": "templates/li_jue.png",
            "caocao": "templates/caocao.png",
            "kill": "templates/kill.png",
            "wusheng": "templates/wusheng.png",
            "zhengnan": "templates/zhengnan.png",
            "small_kill": "templates/small_kill.png",
            "card_change": "templates/card_change.png",
            "trustee": "templates/trustee.png",
            "vectory": "templates/vectory.png",
            "return": "templates/return.png",
            "die": "templates/die.png",
            "choose_wusheng": "templates/choose_wusheng.png",
            "xiefang": "templates/xiefang.png",
            "fail": "templates/fail.png",
        }

        self.loaded_templates = self._load_templates()
        self.has_kill = False
        self.wusheng_available = False

    def _load_templates(self):
        """加载彩色模板（保留3通道）"""
        loaded = {}
        for name, path in self.templates.items():
            try:
                # 直接读取彩色图（默认3通道）
                template = cv2.imread(path)
                if template is not None and template.size > 0:
                    loaded[name] = template
                else:
                    logger.warning(f"彩色模板加载失败: {path}")
            except Exception as e:
                logger.error(f"加载{name}模板失败: {e}")
        return loaded

    def _random_delay(self):
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def _take_screenshot(self):
        """截取彩色屏幕（3通道）"""
        try:
            pyautogui.screenshot(self.screenshot_path)
            # 读取为彩色图（BGR格式，与OpenCV兼容）
            return cv2.imread(self.screenshot_path)
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    def _find_image(self, template_name, threshold=0.7):
        """彩色图模板匹配"""
        template = self.loaded_templates.get(template_name)
        # 检查模板有效性（非None且非空数组）
        if template is None or template.size == 0:
            logger.warning(f"模板 {template_name} 无效")
            return None

        screenshot = self._take_screenshot()
        if screenshot is None or screenshot.size == 0:
            return None

        # 检查通道数匹配（均为3通道）
        if template.ndim != 3 or screenshot.ndim != 3:
            logger.error(f"模板({template.ndim}通道)与截图({screenshot.ndim}通道)不匹配")
            return None

        # 执行彩色图匹配
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= threshold:
            h, w = template.shape[:2]  # 取高和宽（忽略通道维度）
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)
        return None

    def _find_all_images(self, template_name, threshold=0.7):
        """查找所有彩色模板匹配"""
        template = self.loaded_templates.get(template_name)
        if template is None or template.size == 0:
            return []

        screenshot = self._take_screenshot()
        if screenshot is None or screenshot.size == 0:
            return []

        if template.ndim != 3 or screenshot.ndim != 3:
            return []

        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= threshold)
        matches = []
        for pt in zip(*locations[::-1]):
            h, w = template.shape[:2]
            matches.append((pt[0] + w // 2, pt[1] + h // 2))
        return matches

    def _click_target(self, target_name):
        """点击彩色图目标"""
        loc = self._find_image(target_name)
        if loc:
            pyautogui.click(loc[0], loc[1])
            #self._random_delay()
            logger.info(f"点击{target_name}成功")
            return True
        logger.warning(f"未找到{target_name}彩色模板")
        return False

    def _check_card_exist(self, card_name):
        """检查彩色手牌"""
        cards = self._find_all_images(card_name, threshold=0.7)
        return len(cards) > 0

    def _handle_start_challenge(self):
        logger.info("点击开始挑战按钮（彩色图）")
        if self._click_target("start_challenge"):
            time.sleep(self.step_wait)  # 不加等待可能换卡时逻辑有问题
            return True
        logger.error("无法找到彩色开始挑战模板")
        return False

    def _handle_card_change(self):
        for attempt in range(self.max_card_change):
            time.sleep(0.3)
            if self._check_card_exist("kill"):
                logger.info("手牌已存在杀，停止换卡")
                #time.sleep(self.step_wait)
                if self._click_target("cancel"):
                    time.sleep(self.step_wait)
                    return True

            logger.info(f"开始第{attempt + 1}次换卡")

            if not self._click_target("card_change"):
                return False
            #time.sleep(self.step_wait)

            if not self._click_target("confirm"):
                return False
            #time.sleep(self.step_wait)
        logger.warning("达到最大换卡次数，未获得杀")
        #time.sleep(self.step_wait)
        return self._check_card_exist("kill")

    def _choose_wusheng(self):
        if self._click_target("choose_wusheng"):
            logger.info("选择-武圣")
            #time.sleep(self.step_wait)
            return True
        logger.error("无法找到武圣模板")
        return False

    def run_battle_strategy(self):
        if not self._handle_start_challenge():
            return False

        if not self._handle_card_change():
            logger.error("无法获得杀，进入托管")
            #time.sleep(self.step_wait)
            self._click_target("trustee")

        time.sleep(self.step_wait)
        if self._find_image("xiefang"):
            logger.info("取消-协方")
            self._click_target("cancel")

        while self._find_image("li_jue") and not self._find_image("die"):
            self.has_kill = self._check_card_exist("kill")
            self.wusheng_available = self._find_image("wusheng") is not None

            if self.has_kill and not self.wusheng_available:
                if self._click_target("kill"):
                    #time.sleep(self.step_wait)
                    if self._click_target("caocao"):
                        #time.sleep(self.step_wait)
                        if self._click_target("confirm"):
                            time.sleep(2.5)
                            if self._find_image("zhengnan"):
                                time.sleep(0.3)
                                self._click_target("confirm")
                                time.sleep(0.3)
                                if self._choose_wusheng():
                                    #time.sleep(self.step_wait)
                                    logger.info("1")
                            else:
                                logger.info("2")
                    else:
                        logger.info("无曹操可杀")
                        break
            elif self._click_target("kill"):
                #time.sleep(self.step_wait)
                if self._click_target("li_jue"):
                    #time.sleep(self.step_wait)
                    if self._click_target("confirm"):
                        time.sleep(self.step_wait)
                        logger.info("3")

            elif self._click_target("wusheng"):
                # time.sleep(self.step_wait)
                if self._click_target("small_kill"):
                    # time.sleep(self.step_wait)
                    if self._click_target("li_jue"):
                        time.sleep(0.3)
                        self._click_target("confirm")
                time.sleep(self.step_wait)
                logger.info("4")

            else:
                logger.info("无武圣和杀可用")
                break
            #time.sleep(self.step_wait)
            time.sleep(0.3)
            screen_width, screen_height = pyautogui.size()
            pyautogui.click(screen_width // 2, screen_height // 2)
            logger.info("stay")
            time.sleep(0.5)

        if(self._find_image("die")):
            logger.warning("找到李傕濒死")
        if(not self._find_image("li_jue")) :
            logger.warning("未找到李傕")

        logger.info("进入托管阶段")
        #time.sleep(self.step_wait)
        if not self._click_target("trustee"):
            return False

        return self._handle_victory()

    def _handle_victory(self):
        logger.info("检测胜利状态（彩色图）")

        while not (self._find_image("vectory") or self._find_image("fail")):
            time.sleep(self.step_wait)

        logger.info("检测到胜利界面")
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)
        time.sleep(self.step_wait)
        logger.info("点击屏幕中央")

        if self._click_target("return"):
            logger.info("返回战斗选择界面")
            time.sleep(3)
            return True
        return False

    def run_loop(self):
        logger.info("启动彩色图循环战斗模式")
        while True:
            logger.info("新一轮彩色图战斗开始")
            if not self.run_battle_strategy():
                logger.warning("彩色图战斗失败，5秒后重试")
                time.sleep(5)
                continue

            delay = random.uniform(2, 5)
            logger.info(f"等待{delay:.2f}秒后重启")
            time.sleep(delay)


if __name__ == "__main__":
    logger.info("请将游戏窗口置于前台，3秒后开始彩色图脚本")
    time.sleep(3)
    caf = ColorAutoFight()
    caf.run_loop()