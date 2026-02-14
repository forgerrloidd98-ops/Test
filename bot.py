import logging
import os
import time
import html
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Optional

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, Message,
    ReplyKeyboardMarkup, KeyboardButton, BotCommand
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler, ContextTypes, filters,
)
from telegram.error import Forbidden, BadRequest, TimedOut, RetryAfter, NetworkError

# ── Окружение ──────────────────────────────────────────────────────────────────
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = {int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip().isdigit()}
MODE = os.getenv("MODE", "polling").lower()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "dev-secret")

FEED_ERRORS_CHAT_ID = int(os.getenv("FEED_ERRORS_CHAT_ID", "0") or 0)
FEED_ERRORS_TOPIC_ID = int(os.getenv("FEED_ERRORS_TOPIC_ID", "0") or 0)

# ── Новеллы ────────────────────────────────────────────────────────────────────
NOVELS: Dict[str, int] = {
    "ac": 336967830,
    "adastra": 0,
    "ahj": 0,
    "amitw": 0,
    "aptch": 1351092369,
    "arches": 0,
    "as": 670538680,
    "auc": 494289742,
    "avd": 1360254175,
    "bgad": 1360254175,
    "bs": 0,
    "bsm": 0,
    "bth": 0,
    "burrows": 112986742,
    "cc": 494289742,
    "cienie": 1360254175,
    "chopro": 112986742,
    "choprosta": 112986742,
    "cleaved": 494289742,
    "conway": 1360254175,
    "cw": 0,
    "cycles": 1351092369,
    "dad": 336967830,
    "dawntide": 733344501,
    "dc": 0,
    "dt": 573586386,
    "dwb": 2005031396,
    "dy": 0,
    "ec": 0,
    "echo": 0,
    "eissb": 0,
    "er": 112986742,
    "ersf": 0,
    "exastra": 494289742,
    "fbi": 0,
    "fbtw": 792423369,
    "flfl": 670538680,
    "fafo": 0,
    "fur": 646231660,
    "fwj": 1360254175,
    "gd": 1236892676,
    "gh": 897249661,
    "gwh": 0,
    "ha": 1139020740,
    "helward": 112986742,
    "heso": 494289742,
    "hise": 0,
    "hze": 256335589,
    "icoe": 2023906069,
    "icoml": 1236892676,
    "if": 0,
    "ifs": 1236892676,
    "iwo": 5481531399,
    "interea": 0,
    "khemia": 47456266,
    "kingsguard": 2023906069,
    "lautomne": 1916703564,
    "laranja": 0,
    "limits": 573586386,
    "ls": 1360254175,
    "lwr": 494289742,
    "lyre": 792423369,
    "mc": 0,
    "ne": 792423369,
    "nerus": 0,
    "nl": 1731042870,
    "nmf": 1980970876,
    "ns": 1360254175,
    "ntt": 1360254175,
    "ow": 2005031396,
    "password": 2005031396,
    "pervader": 0,
    "pn": 1360254175,
    "reconnected": 1236892676,
    "repeat": 0,
    "rtf": 494289742,
    "run": 494289742,
    "ryt": 1478790307,
    "sa": 2005031396,
    "satoi": 1236892676,
    "sg": 646231660,
    "sileo": 792423369,
    "silverstone": 0,
    "sl": 0,
    "sn": 0,
    "soulcreek": 897249661,
    "starville": 1360254175,
    "steadfast": 0,
    "sylving": 256335589,
    "ta": 1236892676,
    "tb": 1360254175,
    "tbc": 1236892676,
    "tocn": 494289742,
    "tos": 0,
    "ts": 646231660,
    "tsr": 1360254175,
    "tsrcs": 0,
    "tsrss": 0,
    "twt": 1236892676,
    "undefeated": 1236892676,
    "unveiling": 897249661,
    "vd": 1731042870,
    "ve": 897249661,
    "vm": 862463638,
    "wiky": 1236892676,
    "wyn": 646231660,
    "yb": 646231660,
}
NOVEL_LABELS: Dict[str, str] = {
    "ac": "After Class (#ac)",
    "adastra": "Adastra (#adastra)",
    "ahj": "A Hellish Journey (#ahj)",
    "amitw": "A Masquerade in the Woods (#amitw)",
    "aptch": "A Place to Call Home (#aptch)",
    "arches": "Arches (#arches)",
    "as": "Arcane Shop (#as)",
    "auc": "All Under Control (#auc)",
    "avd": "A Vagrant Disguise (#avd)",
    "bgad": "Between Gods and Demons (#bgad)",
    "bs": "Badtime Stories (#bs)",
    "bsm": "Bitter Sweet Memories (#bsm)",
    "bth": "Beyond the Harbor (#bth)",
    "burrows": "Burrows (#burrows)",
    "cc": "Cryptid Crush (#cc)",
    "cienie": "Cienie (#cienie)",
    "chopro": "Chord Progressions (#chopro)",
    "choprosta": "Chord Progressions: Staccato (#choprosta)",
    "cleaved": "Cleaved (#cleaved)",
    "conway": "Conway (#conway)",
    "cw": "Clawstar Wrestling (#cw)",
    "cycles": "Cycles (#cycles)",
    "dad": "Deers and Deckards (#dad)",
    "dawntide": "DawnTide (#dawntide)",
    "dc": "Dawn Chorus (#dc)",
    "dt": "Distant Travels (#dt)",
    "dwb": "Dinner with Blan (#dwb)",
    "dy": "Dearest you (#dy)",
    "ec": "Eclipse City (#ec)",
    "echo": "Echo (#echo)",
    "eissb": "Echo Interactive Short Story: Benefits (#eissb)",
    "er": "Eden's Reach (#er)",
    "ersf": "Echo: Route 65 (#ersf)",
    "exastra": "Exastra (#exastra)",
    "fbi": "Fueled by insanity (#fbi)",
    "fbtw": "Far Beyond the World (#fbtw)",
    "flfl": "Flaming Flagon (#flfl)",
    "fafo": "Fatal Force (#fafo)",
    "fur": "Furry university rebirth (#fur)",
    "fwj": "Four Way Junction (#fwj)",
    "gd": "Gamer Den (#gd)",
    "gh": "Glory Hounds (#gh)",
    "gwh": "Gnoll Way Home (#gwh)",
    "ha": "Hero's Advent (#ha)",
    "helward": "Helward (#helward)",
    "heso": "Heat Source (#heso)",
    "hise": "High Seas (#hise)",
    "hze": "Home Zomewhere Else (#hze)",
    "icoe": "In case of Emergency (#icoe)",
    "icoml": "I.C.O. - Machina Lutris (#icoml)",
    "if": "Integrity's Fall (#if)",
    "ifs": "In Finite Space (#ifs)",
    "iwo": "I Want Out!! (#iwo)",
    "interea": "Interea (#interea)",
    "khemia": "Khemia (#khemia)",
    "kingsguard": "Kingsguard (#kingsguard)",
    "lautomne": "L'Automne (#lautomne)",
    "laranja": "Laranja (#laranja)",
    "limits": "Limits (#limits)",
    "ls": "Lust Shards (#ls)",
    "lwr": "Lunch with Ronan (#lwr)",
    "lyre": "Lyre (#lyre)",
    "mc": "Moonlight Castle (#mc)",
    "ne": "Nowhere's End (#ne)",
    "nerus": "Nerus (#nerus)",
    "nl": "Northern Lights (#nl)",
    "nmf": "No more future (#nmf)",
    "ns": "Next Step (#ns)",
    "ntt": "9:22 (#ntt)",
    "ow": "Outland Wanderer (#ow)",
    "password": "Password (#password)",
    "pervader": "Pervader (#pervader)",
    "pn": "Polar Night (#pn)",
    "reconnected": "Reconnected (#reconnected)",
    "repeat": "Repeat (#repeat)",
    "rtf": "Remember the Flowers (#rtf)",
    "run": "RUN (#run)",
    "ryt": "Roads Yet Traveled (#ryt)",
    "sa": "Socially Awkward (#sa)",
    "satoi": "Sparks: A Tale of Ink (#satoi)",
    "sg": "Scary Gourmet (#sg)",
    "sileo": "Sileo (#sileo)",
    "silverstone": "Silverstone (#silverstone)",
    "sl": "Santa Lucia (#sl)",
    "sn": "Super Nova (#sn)",
    "soulcreek": "Soulcreek (#soulcreek)",
    "starville": "Starville (#starville)",
    "steadfast": "Steadfast (#steadfast)",
    "sylving": "Sylving (#sylving)",
    "ta": "Tennis Ace (#ta)",
    "tb": "Temptation's Ballad (#tb)",
    "tbc": "The Blue Cloth (#tbc)",
    "tocn": "That One Celestial Night (#tocn)",
    "tos": "Tavern of Spear (#tos)",
    "ts": "The Slums (#ts)",
    "tsr": "The Smoke Room (#tsr)",
    "tsrcs": "The Smoke Room: Christmas Special (#tsrcs)",
    "tsrss": "The Smoke Room: Summer Special (#tsrss)",
    "twt": "The Wayward Tower (#twt)",
    "undefeated": "Undefeated (#undefeated)",
    "unveiling": "Unveiling (#unveiling)",
    "vd": "Void Dreaming (#vd)",
    "ve": "Vulgor's exchange (#ve)",
    "vm": "Violet Memoir (#vm)",
    "wiky": "When I Knew you (#wiky)",
    "wyn": "What's your name? (#wyn)",
    "yb": "Yoga Bear (#yb)",
}

# ── Константы меню ─────────────────────────────────────────────────────────────
BTN_START = "📝 Начать отчёт"
BTN_SEND  = "📤 Отправить отчёт"
BTN_CANCEL= "❌ Отмена"

MENU_KB = ReplyKeyboardMarkup(
    [
        [KeyboardButton(BTN_START)],
        [KeyboardButton(BTN_SEND)],
        [KeyboardButton(BTN_CANCEL)],
    ],
    resize_keyboard=True, one_time_keyboard=False, selective=False
)

# ── Диалог ─────────────────────────────────────────────────────────────────────
CHOOSE_NOVEL, COLLECT_MESSAGES = range(2)

# ── Антифлуд ───────────────────────────────────────────────────────────────────
user_last_action_ts: Dict[int, float] = {}
def rate_limited(user_id: int, cooldown_sec: int = 3) -> bool:
    now = time.time()
    prev = user_last_action_ts.get(user_id, 0)
    if now - prev < cooldown_sec:
        return True
    user_last_action_ts[user_id] = now
    return False

# ── Модель состояния ───────────────────────────────────────────────────────────
@dataclass
class PendingReport:
    code: Optional[str] = None
    msgs: list[Message] = field(default_factory=list)

ACK_TTL   = 15
DONE_TTL  = 10
CANCEL_TTL= 7

async def _autodelete_after(bot, chat_id: int, message_id: int, seconds: int):
    try:
        await asyncio.sleep(seconds)
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logging.debug(f"Autodelete failed ({chat_id}:{message_id}): {e}")

def schedule_autodelete(context: ContextTypes.DEFAULT_TYPE, message: Message, seconds: int):
    asyncio.create_task(_autodelete_after(context.bot, message.chat_id, message.message_id, seconds))

def build_novel_keyboard() -> InlineKeyboardMarkup:
    items = sorted(NOVEL_LABELS.items(), key=lambda kv: kv[1].lower())
    rows, row = [], []
    for i, (code, label) in enumerate(items, start=1):
        row.append(InlineKeyboardButton(label, callback_data=f"pick:{code}"))
        if i % 2 == 0:
            rows.append(row); row=[]
    if row: rows.append(row)
    rows.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)

def extract_hashtag_code(text: str) -> Optional[str]:
    if not text:
        return None
    for w in text.lower().split():
        if w.startswith("#"):
            code = w[1:]
            if code in NOVELS:
                return code
    return None

async def forward_message(msg: Message, target_chat_id: int):
    try:
        await msg.forward(chat_id=target_chat_id)
    except Exception as e:
        logging.exception("Forward failed: %s", e)

# ── Сервис ─────────────────────────────────────────────────────────────────────
async def _chat_name_and_url(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> tuple[str, Optional[str]]:
    try:
        chat = await context.bot.get_chat(chat_id)
        name = chat.title or chat.full_name or chat.username or "❓Безымянный"
        url = None
        if getattr(chat, "username", None):
            url = f"https://t.me/{chat.username}"
        elif chat.type == "private" and chat_id > 0:
            url = f"tg://user?id={chat_id}"
        return name, url
    except Exception as e:
        logging.warning(f"Не удалось получить данные чата {chat_id}: {e}")
        return "❓(неизвестно)", None

async def send_report_to_chat(
    context: ContextTypes.DEFAULT_TYPE,
    code: str,
    from_user_id: int,
    from_user_name: str,
    messages: list[Message],
    target_chat_id: int,
    topic_id: int = 0,
):
    header = (
        f"📬 Репорт по новелле: <b>{html.escape(NOVEL_LABELS.get(code, code))}</b>\n"
        f"От: <a href='tg://user?id={from_user_id}'>{html.escape(from_user_name or 'пользователь')}</a>"
    )
    await context.bot.send_message(
        chat_id=target_chat_id,
        text=header,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        message_thread_id=(topic_id or None),
    )
    for m in messages:
        try:
            await m.forward(chat_id=target_chat_id, message_thread_id=(topic_id or None))
        except Exception as e:
            logging.exception("Forward to feed failed: %s", e)

# ── Команды ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Привет! Я пересылаю репорты об ошибках переводчикам.\n\n"
        f"• Нажми «{BTN_START}», выбери новеллу и присылай сообщения/фото.\n"
        "• Или добавь к сообщению хэштег новеллы (например: «Нашёл опечатку #aptch»).\n"
        f"• Когда закончишь — «{BTN_SEND}».\n",
        reply_markup=MENU_KB,
    )

async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    await update.effective_message.reply_html(
        f"🪪 chat_id: <code>{chat.id}</code>\n"
        f"👤 user_id: <code>{user.id}</code>\n"
        f"Тип чата: {chat.type}"
    )

# ── Диалог /report ─────────────────────────────────────────────────────────────
async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if rate_limited(update.effective_user.id):
        return
    context.user_data["pending"] = PendingReport()
    await update.effective_message.reply_text("Выбери новеллу:", reply_markup=build_novel_keyboard())
    return CHOOSE_NOVEL

async def pick_novel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, code = q.data.split(":", 1)
    if code not in NOVELS:
        await q.edit_message_text("Неизвестная новелла. Отменено.")
        return ConversationHandler.END

    pending: PendingReport = context.user_data.get("pending")
    if not pending:
        pending = PendingReport()
    pending.code = code
    context.user_data["pending"] = pending

    await q.edit_message_text(
        f"Новелла: {NOVEL_LABELS.get(code, code)}\n\n"
        f"Пришли сообщения с ошибками. Когда закончишь — нажми «{BTN_SEND}» или команду /send."
    )
    return COLLECT_MESSAGES

async def collect_any(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending: PendingReport = context.user_data.get("pending")
    msg = update.effective_message
    text = (msg.text or msg.caption or "")
    code = extract_hashtag_code(text)

    if not ((pending and pending.code) or code):
        return ConversationHandler.END

    if rate_limited(update.effective_user.id, cooldown_sec=3):
        if pending and pending.code:
            m = await msg.reply_text("⏱ Подожди пару секунд перед новым репортом.")
            schedule_autodelete(context, m, ACK_TTL)
        return ConversationHandler.END

    if not (pending and pending.code):
        target_chat_id = NOVELS.get(code, 0)
        if target_chat_id:
            await forward_message(msg, target_chat_id)
        if FEED_ERRORS_CHAT_ID:
            try:
                await send_report_to_chat(
                    context=context,
                    code=code,
                    from_user_id=update.effective_user.id,
                    from_user_name=update.effective_user.first_name,
                    messages=[msg],
                    target_chat_id=FEED_ERRORS_CHAT_ID,
                    topic_id=FEED_ERRORS_TOPIC_ID,
                )
            except Exception as e:
                logging.exception("Send to feed failed: %s", e)
        ack = await msg.reply_text(f"✅ Репорт отправлен переводчику для {NOVEL_LABELS.get(code, code)}.")
        schedule_autodelete(context, ack, ACK_TTL)
        return ConversationHandler.END

    pending.msgs.append(msg)
    context.user_data["pending"] = pending
    note = await msg.reply_text(f"Принял. Можешь отправить ещё или нажми «{BTN_SEND}».")
    schedule_autodelete(context, note, ACK_TTL)
    return COLLECT_MESSAGES

async def send_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending: PendingReport = context.user_data.get("pending")
    if not pending or not pending.code or not pending.msgs:
        await update.effective_message.reply_text("❌ Нет сообщений для отправки.")
        return ConversationHandler.END

    code = pending.code
    target_chat_id = NOVELS.get(code, 0)

    if target_chat_id:
        header = (
            f"📬 Репорт по новелле: <b>{NOVEL_LABELS.get(code, code)}</b>\n"
            f"От: <a href='tg://user?id={update.effective_user.id}'>{update.effective_user.first_name}</a>"
        )
        try:
            await context.bot.send_message(
                chat_id=target_chat_id, text=header,
                parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            for m in pending.msgs:
                try:
                    await forward_message(m, target_chat_id)
                except (Forbidden, BadRequest, TimedOut, RetryAfter, NetworkError) as e:
                    logging.exception("Forward to translator failed: %s", e)
        except Exception as e:
            logging.exception("Translator DM failed: %s", e)

    if FEED_ERRORS_CHAT_ID:
        try:
            await send_report_to_chat(
                context=context,
                code=code,
                from_user_id=update.effective_user.id,
                from_user_name=update.effective_user.first_name,
                messages=pending.msgs,
                target_chat_id=FEED_ERRORS_CHAT_ID,
                topic_id=FEED_ERRORS_TOPIC_ID,
            )
        except Exception as e:
            logging.exception("Send to feed failed: %s", e)

    await update.effective_message.reply_text("✅ Репорт передан переводчику 🙌")
    context.user_data["pending"] = None
    return ConversationHandler.END

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pending"] = None
    await update.effective_message.reply_text("Отчёт отменён.")
    return ConversationHandler.END

# ── Меню-кнопки (Reply Keyboard) ───────────────────────────────────────────────
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt == BTN_START:
        return await report_cmd(update, context)
    elif txt == BTN_SEND:
        return await send_cmd(update, context)
    elif txt == BTN_CANCEL:
        return await cancel_cmd(update, context)
    # если это не наша кнопка — ничего не делаем

# ── Админка ─────────────────────────────────────────────────────────
def _group_targets_by_chat() -> dict[int, list[str]]:
    by_chat: dict[int, list[str]] = {}
    for code, chat_id in NOVELS.items():
        by_chat.setdefault(chat_id, []).append(code)
    return by_chat

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет прав.")
        return
    if not context.args:
        await update.message.reply_text(
            "Используй: /broadcast <текст>\n"
            "Опции:\n"
            "  /broadcast -codes aptch,soulcreek <текст>\n"
            "  /broadcast -silent <текст>"
        ); return

    args = context.args[:]
    target_codes: set[str] | None = None
    disable_notification = False
    i = 0
    while i < len(args):
        if args[i] == "-codes" and i + 1 < len(args):
            target_codes = set([c.strip().lower() for c in args[i+1].split(",") if c.strip()])
            del args[i:i+2]; continue
        if args[i] == "-silent":
            disable_notification = True
            del args[i]; continue
        i += 1

    text = " ".join(args).strip()
    if not text:
        await update.message.reply_text("Пустой текст. Используй: /broadcast <текст>")
        return

    by_chat = _group_targets_by_chat()
    if target_codes is not None:
        filtered: dict[int, list[str]] = {}
        for chat_id, codes in by_chat.items():
            keep = [c for c in codes if c in target_codes]
            if keep: filtered[chat_id] = keep
        by_chat = filtered

    ok, fail = 0, 0
    for chat_id, codes in by_chat.items():
        if chat_id == 0: continue
        novels_line = ", ".join(NOVEL_LABELS.get(c, c) for c in sorted(codes))
        header = f"📢 Сообщение от админа\nТвои новеллы: {novels_line}\n\n"
        try:
            await context.bot.send_message(chat_id=chat_id, text=header + text, disable_notification=disable_notification)
            ok += 1
        except Exception:
            fail += 1

    msg = await update.message.reply_text(f"✅ Отправлено: {ok}, ❌ Ошибок: {fail}")
    schedule_autodelete(context, msg, ACK_TTL)

async def listnovels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет прав."); return
    if not NOVELS:
        await update.message.reply_text("❌ Список новелл пуст."); return

    MAX_HTML_LEN = 3500
    lines = []
    for code, chat_id in sorted(NOVELS.items(), key=lambda kv: NOVEL_LABELS.get(kv[0], kv[0]).lower()):
        label = NOVEL_LABELS.get(code, code)
        if chat_id == 0:
            name_html = "🚫 переводчика нет"
        else:
            try:
                chat = await context.bot.get_chat(chat_id)
                chat_name = chat.title or chat.full_name or chat.username or "❓Безымянный"
                url = None
                if getattr(chat, "username", None):
                    url = f"https://t.me/{chat.username}"
                elif chat.type == "private" and chat_id > 0:
                    url = f"tg://user?id={chat_id}"
                name_html = (f'<a href="{html.escape(url, quote=True)}">{html.escape(chat_name)}</a>' if url
                             else html.escape(chat_name))
            except Exception as e:
                logging.warning(f"Не удалось получить имя/ссылку для {chat_id}: {e}")
                name_html = "❓(неизвестно)"
        lines.append(f"• {html.escape(label)}\n   ↳ {name_html} (<code>{chat_id}</code>)")

    header = "📚 Список новелл:\n"
    footer = ""

    buf, cur_len = [], len(header) + len(footer) + 10
    for line in lines:
        add_len = len(line) + 1
        if cur_len + add_len > MAX_HTML_LEN and buf:
            await update.message.reply_html(header + "\n".join(buf) + footer, disable_web_page_preview=True)
            buf, cur_len = [], len(header) + len(footer) + 10
        buf.append(line); cur_len += add_len
    if buf:
        await update.message.reply_html(header + "\n".join(buf) + footer, disable_web_page_preview=True)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ Нет прав."); return
    if not context.args:
        codes = ", ".join(sorted(NOVELS.keys()))
        await update.message.reply_text(f"Использование: /contact <код>\nДоступные: {codes}")
        return

    code = context.args[0].lower()
    if code not in NOVELS:
        await update.message.reply_text(f"Не знаю новеллу «{code}». Проверь код."); return

    chat_id = NOVELS[code]
    label = NOVEL_LABELS.get(code, code)
    if chat_id == 0:
        await update.message.reply_html(
            f"📇 Контакт для <b>{html.escape(label)}</b>:\n"
            f"↳ 🚫 переводчика сейчас нет\n"
            f"ℹ️ Репорты по этой новелле дублируются в общий чат."
        ); return

    name, url = await _chat_name_and_url(context, chat_id)
    if url:
        text = (f"📇 Контакт для <b>{html.escape(label)}</b>:\n"
                f"↳ <a href=\"{html.escape(url, quote=True)}\">{html.escape(name)}</a>\n"
                f"<code>{chat_id}</code>")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Открыть чат", url=url)]])
        await update.message.reply_html(text, reply_markup=kb, disable_web_page_preview=True)
    else:
        text = (f"📇 Контакт для <b>{html.escape(label)}</b>:\n"
                f"↳ {html.escape(name)}\n"
                f"<code>{chat_id}</code>\n\n"
                f"ℹ️ Прямая ссылка недоступна (приватный чат без @username). "
                f"Открой чат вручную через список диалогов.")
        await update.message.reply_html(text)

# ── Ошибки ─────────────────────────────────────────────────────────────────────
async def errors_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.exception("Update caused error: %s", context.error)

# ── Команды в списке бота ──────────────────────────────────────────────────────
async def set_bot_commands(app):
    base_cmds = [
        BotCommand("start", "Запуск бота"),
        BotCommand("report", "Начать отчёт"),
        BotCommand("send", "Отправить накопленные сообщения"),
        BotCommand("whoami", "Показать chat_id/user_id"),
    ]
    await app.bot.set_my_commands(base_cmds)

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчики
    conv = ConversationHandler(
        entry_points=[CommandHandler("report", report_cmd)],
        states={
            CHOOSE_NOVEL: [
                CallbackQueryHandler(lambda u,c: cancel_cmd(u,c), pattern=r"^cancel$"),
                CallbackQueryHandler(pick_novel, pattern=r"^pick:.+"),
            ],
            COLLECT_MESSAGES: [
                CallbackQueryHandler(lambda u,c: cancel_cmd(u,c), pattern=r"^cancel$"),
                CommandHandler("send", send_cmd),
                MessageHandler(~filters.COMMAND, collect_any),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_cmd),
            # если написали любую другую команду во время диалога — считаем отменой
            MessageHandler(filters.COMMAND & ~filters.Regex(r"^/send(@[A-Za-z0-9_]{1,32})?$"), cancel_cmd),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # Меню-кнопки
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"^({BTN_START}|{BTN_SEND}|{BTN_CANCEL})$"), handle_menu))

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CommandHandler("send", send_cmd))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("listnovels", listnovels))
    app.add_handler(CommandHandler("contact", contact))

    # Диалог /report
    app.add_handler(conv)

    # РЕЗЕРВ: если почему-то не в состоянии диалога, всё равно обрабатываем клики
    app.add_handler(CallbackQueryHandler(pick_novel, pattern=r"^pick:.+"))
    app.add_handler(CallbackQueryHandler(lambda u, c: cancel_cmd(u, c), pattern=r"^cancel$"))
    
    # Автодетект хэштегов
    app.add_handler(MessageHandler(~filters.COMMAND, collect_any))

    app.add_error_handler(errors_handler)
    app.post_init = set_bot_commands

    if MODE == "webhook":
        base_url = os.environ.get("RENDER_EXTERNAL_URL")
        if not base_url:
            raise RuntimeError("На Render должна быть переменная RENDER_EXTERNAL_URL.")
        base_url = base_url.rstrip("/")
        port = int(os.environ.get("PORT", 8000))
        webhook_url = f"{base_url}/{WEBHOOK_SECRET}"
        logging.info(f"Running in WEBHOOK mode on port {port}, webhook -> {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0", port=port,
            url_path=WEBHOOK_SECRET, webhook_url=webhook_url,
            secret_token=WEBHOOK_SECRET,
        )
    else:
        logging.info("Running in POLLING mode")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
