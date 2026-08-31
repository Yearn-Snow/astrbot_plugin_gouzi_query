import json
from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.event.filter import PermissionType
from astrbot.api.star import Context, Star, register
from astrbot.core.star.star_tools import StarTools


@register(
    "astrbot_plugin_gouzi_query",
    "狗子",
    "完全匹配关键词自动回复与独立菜单分页查询系统",
    "1.0.0",
)
class GouziQueryPlugin(Star):

    def __init__(self, context: Context, config):
        super().__init__(context)

        # =====================================================
        # AstrBot 插件配置
        # =====================================================

        self.config = config

        # 关键词回复开关
        self.reply_enabled = config.get(
            "reply_enabled",
            True
        )

        # 菜单开关
        self.menu_enabled = config.get(
            "menu_enabled",
            True
        )

        # =====================================================
        # AstrBot 持久化数据目录
        #
        # 数据不会放在插件目录中。
        #
        # 插件更新：
        # main.py 等代码       → 更新
        #
        # 用户数据：
        # replies.json         → 保留
        # menu.json            → 保留
        #
        # =====================================================

        self.data_dir = Path(
            StarTools.get_data_dir(
                "astrbot_plugin_gouzi_query"
            )
        )

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # =====================================================
        # 两个完全独立的数据文件
        # =====================================================

        self.reply_file = (
            self.data_dir / "replies.json"
        )

        self.menu_file = (
            self.data_dir / "menu.json"
        )

        # =====================================================
        # 兼容旧版本数据
        #
        # 以前的数据在：
        #
        # astrbot_plugin_gouzi_query/data/
        #
        # 如果发现旧数据，就自动复制到新的持久化目录。
        #
        # 只迁移一次，不删除旧文件。
        # =====================================================

        self._migrate_old_data()

        # =====================================================
        # 创建数据文件
        # =====================================================

        self._create_data_files()

        # =====================================================
        # 加载关键词回复
        # =====================================================

        self.replies = self._load_json(
            self.reply_file,
            {}
        )

        # =====================================================
        # 加载菜单
        # =====================================================

        self.menu = self._load_json(
            self.menu_file,
            []
        )

        # =====================================================
        # 日志
        # =====================================================

        logger.info(
            "[狗子查询系统] 插件加载成功"
        )

        logger.info(
            f"[狗子查询系统] "
            f"数据目录：{self.data_dir}"
        )

        logger.info(
            f"[狗子查询系统] "
            f"关键词回复：{len(self.replies)} 条"
        )

        logger.info(
            f"[狗子查询系统] "
            f"菜单内容：{len(self.menu)} 条"
        )

        logger.info(
            f"[狗子查询系统] "
            f"关键词回复："
            f"{'开启' if self.reply_enabled else '关闭'}"
        )

        logger.info(
            f"[狗子查询系统] "
            f"菜单分页："
            f"{'开启' if self.menu_enabled else '关闭'}"
        )

    # =========================================================
    # 旧数据迁移
    # =========================================================

    def _migrate_old_data(self):

        old_data_dir = (
            Path(__file__).parent / "data"
        )

        old_reply_file = (
            old_data_dir / "replies.json"
        )

        old_menu_file = (
            old_data_dir / "menu.json"
        )

        # -----------------------------------------------------
        # 迁移 replies.json
        # -----------------------------------------------------

        if (
            old_reply_file.exists()
            and not self.reply_file.exists()
        ):

            try:

                with open(
                    old_reply_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    old_replies = json.load(file)

                self._save_json(
                    self.reply_file,
                    old_replies
                )

                logger.info(
                    "[狗子查询系统] "
                    "已迁移旧版 replies.json"
                )

            except Exception as error:

                logger.error(
                    "[狗子查询系统] "
                    f"迁移 replies.json 失败：{error}"
                )

        # -----------------------------------------------------
        # 迁移 menu.json
        # -----------------------------------------------------

        if (
            old_menu_file.exists()
            and not self.menu_file.exists()
        ):

            try:

                with open(
                    old_menu_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    old_menu = json.load(file)

                self._save_json(
                    self.menu_file,
                    old_menu
                )

                logger.info(
                    "[狗子查询系统] "
                    "已迁移旧版 menu.json"
                )

            except Exception as error:

                logger.error(
                    "[狗子查询系统] "
                    f"迁移 menu.json 失败：{error}"
                )

    # =========================================================
    # 创建数据文件
    # =========================================================

    def _create_data_files(self):

        if not self.reply_file.exists():

            self._save_json(
                self.reply_file,
                {}
            )

        if not self.menu_file.exists():

            self._save_json(
                self.menu_file,
                []
            )

    # =========================================================
    # 读取 JSON
    # =========================================================

    def _load_json(
        self,
        file_path: Path,
        default
    ):

        try:

            if not file_path.exists():
                return default

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except Exception as error:

            logger.error(
                "[狗子查询系统] "
                f"读取文件失败：{file_path}\n"
                f"错误：{error}"
            )

            return default

    # =========================================================
    # 保存 JSON
    # =========================================================

    def _save_json(
        self,
        file_path: Path,
        data
    ):

        try:

            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    data,
                    file,
                    ensure_ascii=False,
                    indent=4
                )

            return True

        except Exception as error:

            logger.error(
                "[狗子查询系统] "
                f"保存文件失败：{file_path}\n"
                f"错误：{error}"
            )

            return False

    # =========================================================
    # 管理员：添加回复
    # =========================================================

    @filter.command("添加回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def add_reply(
        self,
        event: AstrMessageEvent
    ):

        message = event.message_str

        prefix = "/添加回复"

        content = message[len(prefix):].strip()

        if "|" not in content:

            yield event.plain_result(
                "❌ 格式错误\n\n"
                "正确格式：\n"
                "/添加回复 关键词 | 回答\n\n"
                "例如：\n"
                "/添加回复 你好 | 你好，我是狗子！"
            )

            return

        keyword, reply = content.split(
            "|",
            1
        )

        keyword = keyword.strip()
        reply = reply.strip()

        if not keyword:

            yield event.plain_result(
                "❌ 关键词不能为空。"
            )

            return

        if not reply:

            yield event.plain_result(
                "❌ 回答不能为空。"
            )

            return

        if keyword in self.replies:

            yield event.plain_result(
                "❌ 添加失败\n\n"
                f"关键词「{keyword}」已经存在。\n\n"
                "如需修改，请使用：\n"
                f"/修改回复 {keyword} | 新回答"
            )

            return

        self.replies[keyword] = reply

        if self._save_json(
            self.reply_file,
            self.replies
        ):

            yield event.plain_result(
                "✅ 添加回复成功\n\n"
                f"关键词：{keyword}\n"
                f"回答：{reply}"
            )

        else:

            del self.replies[keyword]

            yield event.plain_result(
                "❌ 保存失败，请检查插件权限。"
            )

    # =========================================================
    # 查询菜单
    # =========================================================

    @filter.command("查询菜单")
    async def query_menu(
        self,
        event: AstrMessageEvent
    ):

        yield event.plain_result(
            "请发送#+数字以获取对应菜单页\n"
            "例如：#1"
        )

    # =========================================================
    # 管理员：修改回复
    # =========================================================

    @filter.command("修改回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def edit_reply(
        self,
        event: AstrMessageEvent
    ):

        content = event.message_str[
            len("/修改回复"):
        ].strip()

        if "|" not in content:

            yield event.plain_result(
                "❌ 格式错误\n\n"
                "/修改回复 关键词 | 新回答"
            )

            return

        keyword, reply = content.split(
            "|",
            1
        )

        keyword = keyword.strip()
        reply = reply.strip()

        if keyword not in self.replies:

            yield event.plain_result(
                "❌ 修改失败\n\n"
                f"没有找到关键词：{keyword}"
            )

            return

        if not reply:

            yield event.plain_result(
                "❌ 新回答不能为空。"
            )

            return

        old_reply = self.replies[keyword]

        self.replies[keyword] = reply

        if self._save_json(
            self.reply_file,
            self.replies
        ):

            yield event.plain_result(
                "✅ 修改回复成功\n\n"
                f"关键词：{keyword}\n"
                f"新回答：{reply}"
            )

        else:

            self.replies[keyword] = old_reply

            yield event.plain_result(
                "❌ 保存失败，请检查插件权限。"
            )

    # =========================================================
    # 管理员：删除回复
    # =========================================================

    @filter.command("删除回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def delete_reply(
        self,
        event: AstrMessageEvent
    ):

        keyword = event.message_str[
            len("/删除回复"):
        ].strip()

        if not keyword:

            yield event.plain_result(
                "❌ 格式错误\n\n"
                "/删除回复 关键词"
            )

            return

        if keyword not in self.replies:

            yield event.plain_result(
                "❌ 删除失败\n\n"
                f"没有找到关键词：{keyword}"
            )

            return

        old_reply = self.replies[keyword]

        del self.replies[keyword]

        if self._save_json(
            self.reply_file,
            self.replies
        ):

            yield event.plain_result(
                "✅ 删除回复成功\n\n"
                f"关键词「{keyword}」已经删除。"
            )

        else:

            self.replies[keyword] = old_reply

            yield event.plain_result(
                "❌ 保存失败，请检查插件权限。"
            )

    # =========================================================
    # 管理员：查看回复
    # =========================================================

    @filter.command("查看回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def list_replies(
        self,
        event: AstrMessageEvent
    ):

        if not self.replies:

            yield event.plain_result(
                "当前没有任何关键词回复。"
            )

            return

        lines = [
            "狗子查询系统 - 关键词回复",
            f"共 {len(self.replies)} 条",
            ""
        ]

        for index, keyword in enumerate(
            self.replies.keys(),
            start=1
        ):

            lines.append(
                f"{index}. {keyword}"
            )

        yield event.plain_result(
            "\n".join(lines)
        )

    # =========================================================
    # 管理员：添加菜单
    # =========================================================

    @filter.command("添加菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def add_menu(
        self,
        event: AstrMessageEvent
    ):

        content = event.message_str[
            len("/添加菜单"):
        ].strip()

        if not content:

            yield event.plain_result(
                "❌ 格式错误\n\n"
                "/添加菜单 内容"
            )

            return

        if content in self.menu:

            yield event.plain_result(
                f"❌ 菜单「{content}」已经存在。"
            )

            return

        self.menu.append(content)

        if self._save_json(
            self.menu_file,
            self.menu
        ):

            yield event.plain_result(
                "✅ 添加菜单成功\n\n"
                f"内容：{content}\n"
                f"当前菜单共 {len(self.menu)} 条"
            )

        else:

            self.menu.pop()

            yield event.plain_result(
                "❌ 保存失败，请检查插件权限。"
            )

    # =========================================================
    # 管理员：修改菜单
    # =========================================================

    @filter.command("修改菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def edit_menu(
        self,
        event: AstrMessageEvent
    ):

        content = event.message_str[
            len("/修改菜单"):
        ].strip()

        if "|" not in content:

            yield event.plain_result(
                "❌ 格式错误\n\n"
                "/修改菜单 原内容 | 新内容"
            )

            return

        old, new = content.split(
            "|",
            1
        )

        old = old.strip()
        new = new.strip()

        if old not in self.menu:

            yield event.plain_result(
                f"❌ 没有找到菜单：{old}"
            )

            return

        if not new:

            yield event.plain_result(
                "❌ 新内容不能为空。"
            )

            return

        index = self.menu.index(old)

        old_value = self.menu[index]

        self.menu[index] = new

        if self._save_json(
            self.menu_file,
            self.menu
        ):

            yield event.plain_result(
                "✅ 修改菜单成功\n\n"
                f"原内容：{old}\n"
                f"新内容：{new}"
            )

        else:

            self.menu[index] = old_value

            yield event.plain_result(
                "❌ 保存失败，请检查插件权限。"
            )

    # =========================================================
    # 管理员：删除菜单
    # =========================================================

    @filter.command("删除菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def delete_menu(
        self,
        event: AstrMessageEvent
    ):

        content = event.message_str[
            len("/删除菜单"):
        ].strip()

        if not content:

            yield event.plain_result(
                "❌ 格式错误\n\n"
                "/删除菜单 内容"
            )

            return

        if content not in self.menu:

            yield event.plain_result(
                f"❌ 没有找到菜单：{content}"
            )

            return

        index = self.menu.index(content)

        self.menu.pop(index)

        if self._save_json(
            self.menu_file,
            self.menu
        ):

            yield event.plain_result(
                "✅ 删除菜单成功\n\n"
                f"内容：{content}"
            )

        else:

            self.menu.insert(
                index,
                content
            )

            yield event.plain_result(
                "❌ 保存失败，请检查插件权限。"
            )

    # =========================================================
    # 管理员：查看菜单
    # =========================================================

    @filter.command("查看菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def list_menu(
        self,
        event: AstrMessageEvent
    ):

        if not self.menu:

            yield event.plain_result(
                "当前没有任何菜单内容。"
            )

            return

        lines = [
            "狗子查询系统 - 菜单",
            f"共 {len(self.menu)} 条",
            ""
        ]

        for index, item in enumerate(
            self.menu,
            start=1
        ):

            lines.append(
                f"{index}. {item}"
            )

        yield event.plain_result(
            "\n".join(lines)
        )

    # =========================================================
    # 用户：#数字 菜单分页
    # =========================================================

    @filter.event_message_type(
        filter.EventMessageType.ALL
    )
    async def show_menu(
        self,
        event: AstrMessageEvent
    ):

        if not self.menu_enabled:
            return

        message = event.message_str.strip()

        if not message.startswith("#"):
            return

        page_text = message[1:]

        if not page_text.isdigit():
            return

        if not self.menu:

            yield event.plain_result(
                "当前菜单为空。"
            )

            return

        page = int(page_text)

        if page <= 0:

            yield event.plain_result(
                "❌ 菜单页码必须大于 0。"
            )

            return

        page_size = 10

        total_pages = (
            len(self.menu)
            + page_size
            - 1
        ) // page_size

        if page > total_pages:

            yield event.plain_result(
                f"❌ 没有第 {page} 页。\n\n"
                f"当前菜单共 {total_pages} 页。"
            )

            return

        start = (
            page - 1
        ) * page_size

        end = start + page_size

        page_items = self.menu[
            start:end
        ]

        lines = [
            f"内容菜单（{page}/{total_pages}）",
            ""
        ]

        for index, item in enumerate(
            page_items,
            start=start + 1
        ):

            lines.append(
                f"{index}. {item}"
            )

        lines.extend(
            [
                "",
                "发送编号以获得对应内容的详情及下载链接，发送#+数字切换菜单页面"
            ]
        )

        yield event.plain_result(
            "\n".join(lines)
        )

    # =========================================================
    # 用户：关键词完全匹配
    # =========================================================

    @filter.event_message_type(
        filter.EventMessageType.ALL
    )
    async def keyword_reply(
        self,
        event: AstrMessageEvent
    ):

        if not self.reply_enabled:
            return

        # 不使用 strip()
        # 实现真正的完全匹配
        message = event.message_str

        if message in self.replies:

            yield event.plain_result(
                self.replies[message]
            )

    # =========================================================
    # 插件停止
    # =========================================================

    async def terminate(self):

        logger.info(
            "[狗子查询系统] 插件已停止"
        )
