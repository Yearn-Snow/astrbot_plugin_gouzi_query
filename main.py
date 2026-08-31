import json
from pathlib import Path

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.event.filter import PermissionType


@register(
    "astrbot_plugin_keyword_reply",
    "蝌蚪",
    "完全匹配关键词自动回复 + 独立菜单分页",
    "1.0.0"
)
class KeywordReplyPlugin(Star):

    def __init__(self, context: Context):
        super().__init__(context)

        # 插件数据目录
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 两个完全独立的数据文件
        self.reply_file = self.data_dir / "replies.json"
        self.menu_file = self.data_dir / "menu.json"

        # 自动创建数据库
        self._create_files()

        # 加载数据
        self.replies = self._load_json(self.reply_file, {})
        self.menu = self._load_json(self.menu_file, [])

        logger.info(
            f"[关键词自动回复] 已加载 "
            f"{len(self.replies)} 条回复，"
            f"{len(self.menu)} 条菜单"
        )

    # =========================================================
    # 数据文件
    # =========================================================

    def _create_files(self):
        """如果数据文件不存在，则自动创建"""

        if not self.reply_file.exists():
            self._save_json(self.reply_file, {})

        if not self.menu_file.exists():
            self._save_json(self.menu_file, [])

    def _load_json(self, file_path: Path, default):
        """读取 JSON"""

        try:
            if not file_path.exists():
                return default

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        except Exception as e:
            logger.error(
                f"[关键词自动回复] 读取文件失败："
                f"{file_path}，{e}"
            )
            return default

    def _save_json(self, file_path: Path, data):
        """保存 JSON"""

        try:
            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

        except Exception as e:
            logger.error(
                f"[关键词自动回复] 保存文件失败："
                f"{file_path}，{e}"
            )

    # =========================================================
    # 管理员：添加回复
    # =========================================================

    @filter.command("添加回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def add_reply(self, event: AstrMessageEvent):

        message = event.message_str

        # 去掉命令
        content = message[len("/添加回复"):].strip()

        if "|" not in content:
            yield event.plain_result(
                "格式错误\n\n"
                "正确格式：\n"
                "/添加回复 关键词 | 回答\n\n"
                "例如：\n"
                "/添加回复 你好 | 你好，我是蝌蚪客服！"
            )
            return

        keyword, reply = content.split("|", 1)

        keyword = keyword.strip()
        reply = reply.strip()

        if not keyword:
            yield event.plain_result("❌ 关键词不能为空")
            return

        if not reply:
            yield event.plain_result("❌ 回答不能为空")
            return

        if keyword in self.replies:
            yield event.plain_result(
                f"❌ 添加失败\n\n"
                f"关键词「{keyword}」已经存在。\n"
                f"如需修改，请使用：\n"
                f"/修改回复 {keyword} | 新回答"
            )
            return

        self.replies[keyword] = reply

        self._save_json(
            self.reply_file,
            self.replies
        )

        yield event.plain_result(
            "✅ 添加回复成功\n\n"
            f"关键词：{keyword}\n"
            f"回答：{reply}"
        )

    # =========================================================
    # 管理员：修改回复
    # =========================================================

    @filter.command("修改回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def edit_reply(self, event: AstrMessageEvent):

        message = event.message_str

        content = message[len("/修改回复"):].strip()

        if "|" not in content:
            yield event.plain_result(
                "格式错误\n\n"
                "正确格式：\n"
                "/修改回复 关键词 | 新回答"
            )
            return

        keyword, reply = content.split("|", 1)

        keyword = keyword.strip()
        reply = reply.strip()

        if keyword not in self.replies:
            yield event.plain_result(
                f"❌ 修改失败\n\n"
                f"没有找到关键词：{keyword}"
            )
            return

        if not reply:
            yield event.plain_result(
                "❌ 新回答不能为空"
            )
            return

        self.replies[keyword] = reply

        self._save_json(
            self.reply_file,
            self.replies
        )

        yield event.plain_result(
            "✅ 修改成功\n\n"
            f"关键词：{keyword}\n"
            f"新回答：{reply}"
        )

    # =========================================================
    # 管理员：删除回复
    # =========================================================

    @filter.command("删除回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def delete_reply(self, event: AstrMessageEvent):

        message = event.message_str

        keyword = message[len("/删除回复"):].strip()

        if not keyword:
            yield event.plain_result(
                "格式错误\n\n"
                "正确格式：\n"
                "/删除回复 关键词"
            )
            return

        if keyword not in self.replies:
            yield event.plain_result(
                f"❌ 删除失败\n\n"
                f"没有找到关键词：{keyword}"
            )
            return

        del self.replies[keyword]

        self._save_json(
            self.reply_file,
            self.replies
        )

        yield event.plain_result(
            f"✅ 删除成功\n\n"
            f"关键词「{keyword}」已经删除。"
        )

    # =========================================================
    # 管理员：查看回复数量
    # =========================================================

    @filter.command("查看回复")
    @filter.permission_type(PermissionType.ADMIN)
    async def list_replies(self, event: AstrMessageEvent):

        if not self.replies:
            yield event.plain_result(
                "当前没有任何关键词回复。"
            )
            return

        lines = [
            "关键词回复列表",
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
    async def add_menu(self, event: AstrMessageEvent):

        message = event.message_str

        content = message[len("/添加菜单"):].strip()

        if not content:
            yield event.plain_result(
                "格式错误\n\n"
                "正确格式：\n"
                "/添加菜单 内容\n\n"
                "例如：\n"
                "/添加菜单 游客须知"
            )
            return

        if content in self.menu:
            yield event.plain_result(
                f"❌ 添加失败\n\n"
                f"菜单「{content}」已经存在。"
            )
            return

        self.menu.append(content)

        self._save_json(
            self.menu_file,
            self.menu
        )

        yield event.plain_result(
            "✅ 添加菜单成功\n\n"
            f"内容：{content}\n"
            f"当前菜单共 {len(self.menu)} 条"
        )

    # =========================================================
    # 管理员：修改菜单
    # =========================================================

    @filter.command("修改菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def edit_menu(self, event: AstrMessageEvent):

        message = event.message_str

        content = message[len("/修改菜单"):].strip()

        if "|" not in content:
            yield event.plain_result(
                "格式错误\n\n"
                "正确格式：\n"
                "/修改菜单 原内容 | 新内容"
            )
            return

        old, new = content.split("|", 1)

        old = old.strip()
        new = new.strip()

        if old not in self.menu:
            yield event.plain_result(
                f"❌ 修改失败\n\n"
                f"没有找到菜单：{old}"
            )
            return

        if not new:
            yield event.plain_result(
                "❌ 新内容不能为空"
            )
            return

        if new in self.menu and new != old:
            yield event.plain_result(
                f"❌ 修改失败\n\n"
                f"菜单「{new}」已经存在。"
            )
            return

        index = self.menu.index(old)

        self.menu[index] = new

        self._save_json(
            self.menu_file,
            self.menu
        )

        yield event.plain_result(
            "✅ 修改菜单成功\n\n"
            f"原内容：{old}\n"
            f"新内容：{new}"
        )

    # =========================================================
    # 管理员：删除菜单
    # =========================================================

    @filter.command("删除菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def delete_menu(self, event: AstrMessageEvent):

        message = event.message_str

        content = message[len("/删除菜单"):].strip()

        if not content:
            yield event.plain_result(
                "格式错误\n\n"
                "正确格式：\n"
                "/删除菜单 内容"
            )
            return

        if content not in self.menu:
            yield event.plain_result(
                f"❌ 删除失败\n\n"
                f"没有找到菜单：{content}"
            )
            return

        self.menu.remove(content)

        self._save_json(
            self.menu_file,
            self.menu
        )

        yield event.plain_result(
            f"✅ 删除菜单成功\n\n"
            f"内容：{content}"
        )

    # =========================================================
    # 管理员：查看菜单
    # =========================================================

    @filter.command("查看菜单")
    @filter.permission_type(PermissionType.ADMIN)
    async def list_menu(self, event: AstrMessageEvent):

        if not self.menu:
            yield event.plain_result(
                "当前没有任何菜单内容。"
            )
            return

        lines = [
            "菜单列表",
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

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def show_menu(self, event: AstrMessageEvent):

        message = event.message_str.strip()

        # 必须严格匹配 #数字
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
            len(self.menu) + page_size - 1
        ) // page_size

        if page > total_pages:
            yield event.plain_result(
                f"❌ 没有第 {page} 页。\n\n"
                f"当前菜单共 {total_pages} 页。"
            )
            return

        start = (page - 1) * page_size
        end = start + page_size

        page_items = self.menu[start:end]

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
                "请根据以上内容发送关键词以查询问题答案，发送#+数字切换菜单页面"
            ]
        )

        yield event.plain_result(
            "\n".join(lines)
        )

    # =========================================================
    # 用户：完全匹配关键词
    # =========================================================

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def keyword_reply(self, event: AstrMessageEvent):

        message = event.message_str

        if message in self.replies:
            yield event.plain_result(
                self.replies[message]
            )

    # =========================================================
    # 插件卸载
    # =========================================================

    async def terminate(self):
        logger.info(
            "[关键词自动回复] 插件已停止"
        )