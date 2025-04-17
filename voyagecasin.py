from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, ChatMemberHandler, filters, MessageHandler
from datetime import datetime, timedelta
import logging
import random
import re
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Disable overly verbose logs from external libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.request").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

active_menus = {}
address_sessions = {}  
privacy_enabled = {}
user_balances = {6562156998: 46.73, 7336513769: 2.08, 7332748925: 2, 7511218042: 4.87} 
game_in_progress = False

CRYPTO_ADDRESSES = {
    'btc': [
        "bc1qpgvaghnc8z7rz0jpsu99su6u07vfl3ctwdeh93",
        "bc1q524nqz56n5a6v2ezffr8gc8vahd6vp6gcaxtu3",
        "bc1qvxufu4nnnec4qjjxnnknpp8dvq6wmq9jva7ju9"
    ],
    'ltc': [
        "LWn6peYMWgdXAbGjeTaTC4HTtZ87m1FYmm",
        "LfaeHWNUuT1f3PaDKs76jDcwRt5NiQAsWm",
        "LWn6peYMWgdXAbGjeTaTC4HTtZ87m1FYmm",
        "ltc1qnpvr76kcunehy3zjxv5ek3xt4xwq84rcm6c8yr",
        "ltc1q9vuq6tltrsjjwnxdvphy6uyyht9tsdll4gvtck",
        "ltc1qeg2fw2st2gz9uhth09tdduy70t4pkahmj2tjdh"
    ],
    'eth': [
        "0x89B4a3CE1A32cCde9E80A643563a7fe6b32FB2b1",
        "0x2b9520f764Bc66861bB22dcea84F9757CF81dD53",
        "0x394bEC3293eDF591bDDe347bCd2a4D08b49E439c",
        "0x4eA71Df1E29F380aA5F6A66Ae34CF17531D6ae0a"
    ],
    'sol': [
        "BsSPE3o9y3mKQor6L7b6NGiGAa3k9nTSqs5wWZjb5N3S",
        "EwRB1EaSTuVvJjRMQwSpoz9dZznX9DHS57wwvRqt5d8",
        "63mBoy6vpRXUuNkmdHLyF4juSK3EKoHJAMqPFBqVhF8m",
        "ByHivxhtMjVPv1h6TtL9rHTXx7EB4ihqq4DxytJXXpPd",
        "vzrJrzkRenW6otDFkSviHgjMoZugMx1k7sk8Hii5TzA",
        "ByHivxhtMjVPv1h6TtL9rHTXx7EB4ihqq4DxytJXXpPd"
    ],
    'usdc_base': [
        "0x9e071AF557323C66247B525207bA739588dD56F9"
    ],
    'usdc_pol': [
        "0x9e071AF557323C66247B525207bA739588dD56F9"
    ],
    'usdc_erc': [
        "0x9e071AF557323C66247B525207bA739588dD56F9"
    ],
    'usdc_sol': [
        "hhjybx1qmmfMrKW6ZD6xfWR9XjFfUz7i6YhCq7USAob"
    ],
    'usdc_bep': [
        "0x9e071AF557323C66247B525207bA739588dD56F9"
    ]
}



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check if the /start command has the 'deposit' or 'withdraw' argument
    if context.args:
        if context.args[0] == 'deposit':
            # If it's a deposit, call the deposit menu
            return await deposit_menu(update, context)
        elif context.args[0] == 'withdraw':
            # If it's a withdraw, call the withdraw menu
            return await withdraw_menu(update, context)

    # Otherwise, show the general start menu
    balance = user_balances.get(user_id, 0)

    keyboard = [
        [InlineKeyboardButton("🎁 Deposit gifts", callback_data='deposit_gifts')],
        [InlineKeyboardButton("🆕📈 Predictions", callback_data='predictions'),
         InlineKeyboardButton("🆕🚀 Crash", callback_data='crash')],
        [InlineKeyboardButton("👥 Join Group", url='https://t.me/DenaroCasinoChat')],
        [InlineKeyboardButton("🎱 Games", callback_data='games')],
        [InlineKeyboardButton("📥 Deposit", callback_data='deposit'),
         InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("💰 Refer and Earn", callback_data='refer')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='settings')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the user's balance
    sent_message = await update.message.reply_text(
        f"<b>Denaro Casino</b>\n\nBalance:  <b>{balance}€</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    active_menus[sent_message.message_id] = user_id

HOUSE_STATE = {"balance": 29058}

async def update_house_balance():
    while True:
        await asyncio.sleep(60)
        change = random.randint(-100, 100)
        HOUSE_STATE["balance"] += change
        # Optional: Clamp to a minimum of 0
        HOUSE_STATE["balance"] = max(HOUSE_STATE["balance"], 0)

async def house_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"House balance: <b>${HOUSE_STATE['balance']}</b>",
        parse_mode="HTML"
    )

# Add this function to start the updater in the background
async def on_startup(app):
    app.create_task(update_house_balance())

async def tip_command(update, context):
    if not context.args:
        await update.message.reply_text(
            "Usage example: <code>/tip 1$ @gaetano</code>",
            parse_mode='HTML'
        )
        return

    tip_text = ' '.join(context.args)
    match = re.match(r'^\d+\$\s*@?\w+$', tip_text)

    if match:
        await update.message.reply_text("Not enough coins, balance is 0$")
    else:
        await update.message.reply_text(
            "Usage example: <code>/tip 1$ @gaetano</code>",
            parse_mode='HTML'
        )
        
        active_menus[sent_message.message_id] = user_id

async def darts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    keyboard = [
        [InlineKeyboardButton("Play", callback_data='play_dart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "<b>Dart</b>\n\n"
        "Play darts against other users or the bot.\n\n"
        "<b>Usage:</b> <code>/dart amount mode</code>\n"
        "<b>Multiplier:</b> <b>1.92x</b> with bot, <b>1.98x</b> with people.\n\n"
        "Examples:\n\n"
        "<code>/dart 5$</code> - first to 3 match for 5$\n"
        "<code>/dart 3$ 2</code> - first to 2 match for 3$\n"
        "<code>/dart 10$ 3d2w</code> - first to 2 match with 3 dart(s) each (values sum) for 10$\n"
        "<code>/dart 10$ 4 crazy</code> - first to 4 crazy mode match (lower roll wins)\n\n"
    )

    # Sende Nachricht + speichere message_id
    sent_message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Nur dieser User darf später auf den Button klicken
    active_menus[sent_message.message_id] = user_id


async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()

    # Find the next Monday at 00:00 UTC
    days_until_monday = (7 - now.weekday()) % 7
    next_monday = datetime.combine(now.date() + timedelta(days=days_until_monday), datetime.min.time())

    # If it's already Monday and past midnight, go to next week's Monday
    if next_monday <= now:
        next_monday += timedelta(days=7)

    time_left = next_monday - now
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Compose the countdown string
    countdown = f"{days} day{'s' if days != 1 else ''}, {hours:02}:{minutes:02}:{seconds:02}"

    text = (
        f"Next weekly bonus redeem available in <b>{countdown}</b>\n\n"
        "Estimated next weekly bonus: <b>0€</b>\n\n"
        "<b>Add @denaro to your name to have your rakeback and weekly boosted!</b>"
    )

    await update.message.reply_text(text, parse_mode="HTML")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # If you’re using user ID tracking

    text = (
        "<b>Withdraw</b>\n\n"
        "There are 14 cryptocurrencies supported for withdrawals.\n\n"
        "Choose your favourite one!"
    )
    keyboard = [
        [InlineKeyboardButton("Bitcoin (BTC)", callback_data='withdraw_btc'),
         InlineKeyboardButton("Litecoin (LTC)", callback_data='withdraw_ltc')],
        [InlineKeyboardButton("Toncoin (TON)", callback_data='withdraw_ton'),
         InlineKeyboardButton("Ethereum (ETH)", callback_data='withdraw_eth')],
        [InlineKeyboardButton("USDT (ERC20)", callback_data='withdraw_usdt_erc20'),
         InlineKeyboardButton("USDC (ERC20)", callback_data='withdraw_usdc_erc20')],
        [InlineKeyboardButton("USDT (POL)", callback_data='withdraw_usdt_pol'),
         InlineKeyboardButton("USDC (POL)", callback_data='withdraw_usdc_pol')],
        [InlineKeyboardButton("Solana (SOL)", callback_data='withdraw_sol'),
         InlineKeyboardButton("Tron (TRX)", callback_data='withdraw_trx')],
        [InlineKeyboardButton("USDT (TRC20)", callback_data='withdraw_usdt_trc20'),
         InlineKeyboardButton("BNB (BEP20)", callback_data='withdraw_bnb_bep20')],
        [InlineKeyboardButton("USDT (BEP20)", callback_data='withdraw_usdt_bep20'),
         InlineKeyboardButton("Monero (XMR)", callback_data='withdraw_xmr')],
        [InlineKeyboardButton("🔙", callback_data='back_to_main')]
    ]

    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


    active_menus[update.message.message_id] = user_id

async def play_dart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Play Dart' button press."""
    query = update.callback_query
    user_id = query.from_user.id
    message_id = query.message.message_id

    # Schutz gegen fremde Klicks
    if message_id in active_menus and active_menus[message_id] != user_id:
     await query.answer()  # Blockiert den Button ohne Nachricht
     return

    await query.answer()

    text = (
     "<b>Choose amount</b>\n\n"
     "How much are you going to bet in this match?\n\n"
    )

    keyboard = [
     [InlineKeyboardButton("Minimum amount is 0.0091$", callback_data='amount_0091')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Bearbeite die Nachricht mit den neuen Optionen
    await query.edit_message_text(
     text=text,
     reply_markup=reply_markup,
     parse_mode="HTML"
    )

    active_menus[message_id] = user_id


async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    keyboard = [
        [InlineKeyboardButton("Play", callback_data='play_dart')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "<b>Dice</b>\n\n"
        "Play dice against other users or the bot.\n\n"
        "<b>Usage:</b> <code>/dice amount mode</code>\n"
        "<b>Multiplier:</b> <b>1.92x</b> with bot, <b>1.98x</b> with people.\n\n"
        "Examples:\n\n"
        "<code>/dice 5$</code> - first to 3 match for 5$\n"
        "<code>/dice 3$ 2</code> - first to 2 match for 3$\n"
        "<code>/dice 10$ 3d2w</code> - first to 2 match with 3 dice(s) each (values sum) for 10$\n"
        "<code>/dice 10$ 4 crazy</code> - first to 4 crazy mode match (lower roll wins)\n\n"
    )

    # Sende Nachricht + speichere message_id
    sent_message = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

    # Nur dieser User darf später auf den Button klicken
    active_menus[sent_message.message_id] = user_id

async def mypreds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Bet again", callback_data="predictions")]
    ])
    await update.message.reply_text(
        "No placed bet",
        reply_markup=keyboard
    )

async def handle_withdraw(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, coin: str, fee: str, minimum: str):
    text = (
        f"<b>Withdraw {coin} to your wallet</b>\n\n"
        f"Fees: <b>{fee}</b>\n\n"
        f"Minimum withdrawal: <b>{minimum}</b>\n\n"
        "Choose withdrawal amount, or send a custom one"
    )

    keyboard = [
        [InlineKeyboardButton("Balance is too low", callback_data="noop")],
        [InlineKeyboardButton("🔙", callback_data="withdraw")]
    ]

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# Map callback data to coin info
withdraw_coin_info = {
    "withdraw_btc": ("Bitcoin (BTC)", "$5", "$6"),
    "withdraw_ltc": ("Litecoin (LTC)", "$0.1", "$1"),
    "withdraw_ton": ("Toncoin (TON)", "$0.1", "$1"),
    "withdraw_eth": ("Ethereum (ETH)", "$0.03", "$5"),
    "withdraw_usdt_erc20": ("USDT (ERC20)", "$0.09", "$10"),
    "withdraw_usdc_erc20": ("USDC (ERC20)", "$0.09", "$10"),
    "withdraw_usdt_pol": ("USDT (POL)", "$0.02", "$1"),
    "withdraw_usdc_pol": ("USDC (POL)", "$0.02", "$1"),
    "withdraw_sol": ("Solana (SOL)", "$0.05", "$1"),
    "withdraw_trx": ("Tron (TRX)", "$0.74", "$5"),
    "withdraw_usdt_trc20": ("USDT (TRC20)", "$7.44", "$30"),
    "withdraw_bnb_bep20": ("BNB (BEP20)", "$0.02", "$1"),
    "withdraw_usdt_bep20": ("USDT (BEP20)", "$0.09", "$5"),
    "withdraw_xmr": ("Monero (XMR)", "$1", "$3"),
}


async def maxbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Maximum allowed bets</b>\n\n"
        "<i>This only applies to bet against the bot. Player vs Player are not affected</i>\n\n"
        "Dice: <b>2553€</b>\n"
        "Mines: <b>606.27€</b>\n"
        "Hilo: <b>616.84€</b>"
    )
    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )

async def sides(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Side Betting</b>\n\n"
        "You can bet on the outcome of a dice match! \n"
        "Reply with <code>/win 5$</code> to a player's message or use <code>/win 5$ @gaetano</code>. "
        "You can use <code>/lose</code> too. Use <code>/sides</code> to see players multipliers."
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Dice stats (last month)</b>\n\n"
        "Matches count: 0\n"
        "Win rate: 0%\n"
        "Wagered: $0\n"
        "Highest bet: $0\n"
        "Average bet: $0\n"
        "PnL: +$0\n\n"
        "Bonuses received: $0\n"
        "Total PnL: +$0\n\n"
        "Use /profile to see your ranking level"
    )
    await update.message.reply_text(text, parse_mode="HTML")
    
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Your profile</b>\n\n"
        "Level: <b>Steel</b>\n"
        "Progress: <b>0%</b> → <b>Iron I</b>\n"
        "▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯▯\n\n"
        "<b>Steel features:</b>\n"
        "Rakeback: 12%\n"
        "Weekly bonus: 1x\n\n"
        "<b>Iron I features:</b>\n"
        "Level-Up bonus: $1\n"
        "Weekly bonus: 1x → 1.03x\n\n"
        "Use /levels to see all the rank levels, benefits and bonuses"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Steel</b>\n\n"
        "Wagered: <b>$0</b>\n\n"
        "Rakeback: 12%\n"
        "Weekly bonus: 1x"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Iron I", callback_data="noop")]
    ])

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)



async def play_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Play Dart' button press."""
    query = update.callback_query
    user_id = query.from_user.id
    message_id = query.message.message_id

    # Schutz gegen fremde Klicks
    if message_id in active_menus and active_menus[message_id] != user_id:
     await query.answer()  # Blockiert den Button ohne Nachricht
     return

    await query.answer()

    text = (
     "<b>Choose amount</b>\n\n"
     "How much are you going to bet in this match?\n\n"
    )

    keyboard = [
     [InlineKeyboardButton("Minimum amount is 0.0091$", callback_data='amount_0091')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Bearbeite die Nachricht mit den neuen Optionen
    await query.edit_message_text(
     text=text,
     reply_markup=reply_markup,
     parse_mode="HTML"
    )

    active_menus[message_id] = user_id
# async def dice(update, context):
#     user_id = update.message.from_user.id
#     context.user_data['dice_user_id'] = user_id  # Store the user_id who initiated the /dice command
    
#     text = (
#         "<b>Dice</b>\n\n"
#         "Play dice against other users or the bot.\n\n"
#         "<b>Usage:</b> <code>/dice amount mode</code>\n"
#         "<b>Multiplier:</b> <b>1.92x</b> with bot, <b>1.98x</b> with people.\n\n"
#         "Examples:\n\n"
#         "<code>/dice 5$</code> - first to 3 match for 5$\n"
#         "<code>/dice 3$ 2</code> - first to 2 match for 3$\n"
#         "<code>/dice 10$ 3d2w</code> - first to 2 match with 3 dice(s) each (values sum) for 10$\n"
#         "<code>/dice 10$ 4 crazy</code> - first to 4 crazy mode match (lower roll wins)\n\n"
#     )

#     # Define the keyboard with the Play button
#     keyboard = [
#         [InlineKeyboardButton("Play", callback_data="play_dice")]
#     ]

#     # Send the message with the explanation and the "Play" button
#     await update.message.reply_text(
#         text=text,
#         reply_markup=InlineKeyboardMarkup(keyboard),
#         parse_mode="HTML"
#     )

# async def play_dice(update, context):
#     query = update.callback_query
#     user_id = query.from_user.id

#     # Ensure that only the user who initiated the /dice command can interact
#     if user_id != context.user_data.get('dice_user_id'):
#         await query.answer("You are not authorized to play this game.", show_alert=True)
#         return

#     # Proceed with the rest of the game logic
#     await choose_game_mode(update, context)

# async def choose_game_mode(update, context):
#     user_id = update.callback_query.from_user.id
#     message_id = update.callback_query.message.message_id

#     # ❗ Schutz gegen fremde Buttonklicks (silent)
#     if message_id in active_menus and active_menus[message_id] != user_id:
#         await update.callback_query.answer()  # stilles Acknowledge, keine Nachricht
#         return

#     # Default settings
#     settings = context.user_data.setdefault('game_settings', {
#         'game': 'dice',
#         'first_to': 3,
#         'rolls': 1,
#         'bet': '0€ - 100%'
#     })

#     query = update.callback_query
#     data = query.data if query else None

#     # Handle inputs
#     if data:
#         await query.answer()

#         if data.startswith('game_'):
#             settings['game'] = data.split('_')[1]
#         elif data.startswith('first_to_'):
#             settings['first_to'] = int(data.split('_')[2])
#         elif data.startswith('rolls_'):
#             settings['rolls'] = int(data.split('_')[1])

#     # Game emoji map
#     game_emojis = {
#         'dice': '🎲',
#         'bowling': '🎳',
#         'dart': '🎯',
#         'football': '⚽',
#         'basketball': '🏀'
#     }

#     emoji = game_emojis.get(settings['game'], '🎲')

#     # Text to display
#     text = f"""
# {emoji} <b>{settings['game'].capitalize()}</b>
# Match against the bot, {settings['rolls']} roll(s) each.
# First to reach {settings['first_to']} rounds wins.

# Multiplier: 1.92x  
# Winning chance: 50%  

# Balance: 0€
# """.strip()

#     # --- Button Rendering: ✅ Tick Logic ---
#     keyboard = [
#         [InlineKeyboardButton("Game", callback_data='noop')],
#         [
#             InlineKeyboardButton(f"🎲{' ✅' if settings['game'] == 'dice' else ''}", callback_data='game_dice'),
#             InlineKeyboardButton(f"🎳{' ✅' if settings['game'] == 'bowling' else ''}", callback_data='game_bowling'),
#             InlineKeyboardButton(f"🎯{' ✅' if settings['game'] == 'dart' else ''}", callback_data='game_dart'),
#             InlineKeyboardButton(f"⚽{' ✅' if settings['game'] == 'football' else ''}", callback_data='game_football'),
#             InlineKeyboardButton(f"🏀{' ✅' if settings['game'] == 'basketball' else ''}", callback_data='game_basketball'),
#         ],

#         [InlineKeyboardButton("First to", callback_data='noop')],
#         [
#             InlineKeyboardButton(f"1{' ✅' if settings['first_to'] == 1 else ''}", callback_data='first_to_1'),
#             InlineKeyboardButton(f"2{' ✅' if settings['first_to'] == 2 else ''}", callback_data='first_to_2'),
#             InlineKeyboardButton(f"3{' ✅' if settings['first_to'] == 3 else ''}", callback_data='first_to_3'),
#             InlineKeyboardButton(f"4{' ✅' if settings['first_to'] == 4 else ''}", callback_data='first_to_4'),
#             InlineKeyboardButton(f"5{' ✅' if settings['first_to'] == 5 else ''}", callback_data='first_to_5'),
#         ],

#         [InlineKeyboardButton("Rolls count", callback_data='noop')],
#         [
#             InlineKeyboardButton(f"1{' ✅' if settings['rolls'] == 1 else ''}", callback_data='rolls_1'),
#             InlineKeyboardButton(f"2{' ✅' if settings['rolls'] == 2 else ''}", callback_data='rolls_2'),
#             InlineKeyboardButton(f"3{' ✅' if settings['rolls'] == 3 else ''}", callback_data='rolls_3'),
#         ],

#         [InlineKeyboardButton("Bet amount", callback_data='noop')],
#         [InlineKeyboardButton(f"{settings['bet']}", callback_data='set_bet')],

#         [InlineKeyboardButton("Back", callback_data='back_to_mainP')]
#     ]

#     # Respond with updated inline keyboard
#     await query.edit_message_text(
#         text=text,
#         reply_markup=InlineKeyboardMarkup(keyboard),
#         parse_mode="HTML"
#     )

#     # Speichert die message_id und user_id für den Schutz gegen fremde Klicks
#     active_menus[update.callback_query.message.message_id] = user_id



    
async def depo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    crypto_map = {
        'btc': 'deposit_btc',
        'ltc': 'deposit_ltc',
        'eth': 'deposit_eth',
        'sol': 'deposit_sol',
    }

    # Dummy async function for answer()
    async def dummy_answer(*args, **kwargs):
        pass

    # Dummy Message with message_id
    class DummyMessage:
        def __init__(self, reply_func, chat):
            self.message_id = update.message.message_id
            self.reply_text = reply_func
            self.chat = chat  # Add this line to simulate the chat attribute

    # Simulate a full FakeQuery including the chat type
    def create_fake_query(data, reply_func, chat):
        return type('FakeQuery', (), {
            'data': data,
            'answer': dummy_answer,
            'edit_message_text': reply_func,
            'message': DummyMessage(reply_func, chat),
            'from_user': update.message.from_user,
            '_from_command': True  # key difference!
        })()

    # Modify the section where you create the fake query
    if args and args[0].lower() in crypto_map:
        coin = args[0].lower()
        fake_query = create_fake_query(crypto_map[coin], update.message.reply_text, update.message.chat)
    else:
        fake_query = create_fake_query('deposit', update.message.reply_text, update.message.chat)

    # Simulate a CallbackQuery-Update
    fake_update = type('FakeUpdate', (), {'callback_query': fake_query})()
    await button_handler(fake_update, context)



async def show_balance(update: Update, context):
    user_id = update.message.from_user.id

    # Get the balance for the user, default to 0 if no balance is found
    balance = user_balances.get(user_id, 0)

    # Format the balance with bold HTML tags
    balance_text = f"Balance: <b>{balance}€</b>"

    # Create the inline keyboard with Deposit and Withdraw buttons
    keyboard = [
        [
            InlineKeyboardButton("📥Deposit", url="https://t.me/denarocasinbot?start=deposit"),  # Clicking this will send /start deposit
            InlineKeyboardButton("📤Withdraw", url="https://t.me/denarocasinbot?start=withdraw")  # Clicking this will send /start withdraw
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the balance and the buttons
    await update.message.reply_text(
        text=balance_text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def withdraw_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    text = (
        "<b>Withdraw</b>\n\n"
        "There are 14 cryptocurrencies supported for withdrawals.\n\n"
        "Choose your favourite one!"
    )

    keyboard = [
        [InlineKeyboardButton("Bitcoin (BTC)", callback_data='withdraw_btc'),
         InlineKeyboardButton("Litecoin (LTC)", callback_data='withdraw_ltc')],
        [InlineKeyboardButton("Toncoin (TON)", callback_data='withdraw_ton'),
         InlineKeyboardButton("Ethereum (ETH)", callback_data='withdraw_eth')],
        [InlineKeyboardButton("USDT (ERC20)", callback_data='withdraw_usdt_erc20'),
         InlineKeyboardButton("USDC (ERC20)", callback_data='withdraw_usdc_erc20')],
        [InlineKeyboardButton("USDT (POL)", callback_data='withdraw_usdt_pol'),
         InlineKeyboardButton("USDC (POL)", callback_data='withdraw_usdc_pol')],
        [InlineKeyboardButton("Solana (SOL)", callback_data='withdraw_sol'),
         InlineKeyboardButton("Tron (TRX)", callback_data='withdraw_trx')],
        [InlineKeyboardButton("USDT (TRC20)", callback_data='withdraw_usdt_trc20'),
         InlineKeyboardButton("BNB (BEP20)", callback_data='withdraw_bnb_bep20')],
        [InlineKeyboardButton("USDT (BEP20)", callback_data='withdraw_usdt_bep20'),
         InlineKeyboardButton("Monero (XMR)", callback_data='withdraw_xmr')],
        [InlineKeyboardButton("🔙", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the withdraw menu to the user
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def deposit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    text = (
        "<b>Deposit - no minimum amount</b>\n\n"
        "Deposits are credited as soon as 1 blockchain confirmation is reached.\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("🎁 Deposit Telegram Gifts", callback_data='deposit_gifts')],
        [InlineKeyboardButton("Bitcoin (BTC)", callback_data='deposit_btc'),
         InlineKeyboardButton("Litecoin (LTC)", callback_data='deposit_ltc')],
        [InlineKeyboardButton("Dogecoin (DOGE)", callback_data='deposit_doge'),
         InlineKeyboardButton("Ethereum (ETH)", callback_data='deposit_eth')],
        [InlineKeyboardButton("Tron (TRX)", callback_data='deposit_trx'),
         InlineKeyboardButton("BNB (BNB)", callback_data='deposit_bnb')],
        [InlineKeyboardButton("Ripple (XRP)", callback_data='deposit_xrp'),
         InlineKeyboardButton("Polygon (POL)", callback_data='deposit_pol')],
        [InlineKeyboardButton("Ethereum (BASE)", callback_data='deposit_base'),
         InlineKeyboardButton("Solana (SOL)", callback_data='deposit_sol')],
        [InlineKeyboardButton("Toncoin (TON)", callback_data='deposit_ton'),
         InlineKeyboardButton("Monero (XMR)", callback_data='deposit_xmr')],
        [InlineKeyboardButton("USDT (TON)", callback_data='deposit_usdt_ton'),
         InlineKeyboardButton("USDT (TRC20)", callback_data='deposit_usdt_trc20')],
        [InlineKeyboardButton("USDT (ERC20)", callback_data='deposit_usdt_erc20'),
         InlineKeyboardButton("USDC (ERC20)", callback_data='deposit_usdc_erc20')],
        [InlineKeyboardButton("USDT (BEP20)", callback_data='deposit_usdt_bep20'),
         InlineKeyboardButton("USDC (BEP20)", callback_data='deposit_usdc_bep20')],
        [InlineKeyboardButton("USDC (BASE)", callback_data='deposit_usdc_base'),
         InlineKeyboardButton("USDT (SOL)", callback_data='deposit_usdt_sol')],
        [InlineKeyboardButton("USDC (SOL)", callback_data='deposit_usdc_sol'),
         InlineKeyboardButton("TRUMP (SOL)", callback_data='deposit_trump_sol')],
        [InlineKeyboardButton("USDT (POL)", callback_data='deposit_usdt_pol'),
         InlineKeyboardButton("USDC (POL)", callback_data='deposit_usdc_pol')],
        [InlineKeyboardButton(" Apple Pay", callback_data='deposit_applepay'),
         InlineKeyboardButton("🅿️ PayPal", callback_data='deposit_paypal')],
        [InlineKeyboardButton("®️ Revolut", callback_data='deposit_revolut'),
         InlineKeyboardButton("w Wise", callback_data='deposit_wise')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the deposit menu to the user
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )


async def detect_group_add(update, context):
    # Check if this is a new chat member event and if the bot is among them
    if update.message and update.message.new_chat_members:
        for user in update.message.new_chat_members:
            if user.id == context.bot.id:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=(
                            "Thank you for adding me there!\n\n"
                            "Use /dice and /rps to play in this group\n\n"
                            "Group owner will earn 40% of commissions generated by this group directly in his bot balance.\n\n"
                            "Deposit in bot using /deposit"
                        )
                    )
                    logger.info(f"Welcome message sent to group {update.effective_chat.id}")
                except Exception as e:
                    logger.error(f"Failed to send welcome message: {e}")


async def button_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    message_id = query.message.message_id
    
    user = query.from_user
    logger.info(
    f"User {user.id} (@{user.username}) clicked: {query.data}"
)

    if message_id in active_menus and active_menus.get(message_id) != user_id:
        return  

    await query.answer()

    if query.data == 'deposit_gifts':
        text = (
            "📦 <b>Gifts Deposit</b>\n\n"
            "Transfer the gift to <a href='https://t.me/gaetano'>@gaetano</a> and the deposit amount will be "
            "automatically credited to your balance!\n\n"
            "You will also be able to buy your gift back for a small fee."
        )
        keyboard = [
            [InlineKeyboardButton("💰 Deposit amount for each gift", callback_data='gift_amount')],
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

    elif query.data == 'predictions':
        text = "📉 <b>Prediction betting</b>"
        keyboard = [
            [InlineKeyboardButton("Bitcoin price on April 11?", callback_data='pred_1')],
            [InlineKeyboardButton("Trump ends Ukraine war in first 90 days?", callback_data='pred_2')],
            [InlineKeyboardButton("Will Trump create Bitcoin reserve in first 100 days?", callback_data='pred_3')],
            [InlineKeyboardButton("Trump Admin confirms Aliens exist in first 100 days?", callback_data='pred_4')],
            [InlineKeyboardButton("Will Putin meet with Trump in first 100 days?", callback_data='pred_5')],
            [InlineKeyboardButton("Who will Trump pardon in first 100 days?", callback_data='pred_6')],
            [InlineKeyboardButton("Will TikTok be banned again before May?", callback_data='pred_7')],
            [InlineKeyboardButton("What price will Ethereum hit in April?", callback_data='pred_8')],
            [InlineKeyboardButton("Will Trump audit Ukraine aid before May?", callback_data='pred_9')],
            [InlineKeyboardButton("What price will Bitcoin hit in April?", callback_data='pred_10')],
            [InlineKeyboardButton("What price will Solana hit in April?", callback_data='pred_11')],
            [InlineKeyboardButton("TikTok sale announced before May?", callback_data='pred_12')],
            [InlineKeyboardButton("What price will XRP hit in April?", callback_data='pred_13')],
            [InlineKeyboardButton("Eurovision Winner 2025", callback_data='pred_14')],
            [InlineKeyboardButton("Europa League Winner", callback_data='pred_15')],
            [InlineKeyboardButton("Serie A Winner", callback_data='pred_16')],
            [InlineKeyboardButton("Premier League: Top 4 finishers", callback_data='pred_17')],
            [InlineKeyboardButton("La Liga Winner", callback_data='pred_18')],
            [InlineKeyboardButton("English Premier League Top Scorer", callback_data='pred_19')],
            [InlineKeyboardButton("Premier League 2nd Place", callback_data='pred_20')],
            [InlineKeyboardButton("Champions League Winner", callback_data='pred_21')],
            [InlineKeyboardButton("NBA MVP", callback_data='pred_22')],
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

    elif query.data == 'crash':
        await query.edit_message_text(
            text="🚧 <b>Crash game</b>\n\nThis feature is currently not available. Please check back soon!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙", callback_data='back_to_main')]
            ])
        )
        
        active_menus[query.message.message_id] = user_id

        
    elif query.data == 'games':
        text = "<b>Games</b>\n\nChoose between emojis-based games and regular ones, all provably fair!"
        keyboard = [
            [InlineKeyboardButton("🎲 Emoji Casino", callback_data='emoji_casino'),
             InlineKeyboardButton("💣 Regular Games", callback_data='regular_games')],
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

    elif query.data == 'emoji_casino':
        text = (
            "<b>Emoji Games</b>\n\n"
            "Choose between a variety of different games, all based on telegram-generated emojis!\n\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔮 Predict", callback_data='play_predict')],  # Full width button
            [InlineKeyboardButton("🎲 Dice", callback_data='play_dice')],      # Full width button
            [InlineKeyboardButton("🎳 Bowling", callback_data='play_bowling'),
             InlineKeyboardButton("🎯 Dart", callback_data='play_dart')],
            [InlineKeyboardButton("⚽ Soccer", callback_data='play_soccer'),
             InlineKeyboardButton("🏀 Basket", callback_data='play_basket')],
            [InlineKeyboardButton("🎰 Single Emoji Games", callback_data='play_single')],
            [InlineKeyboardButton("🔙", callback_data='games')]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

    elif query.data == 'regular_games':
        text = (
            "<b>Regular Games</b>\n\n"
            "Not only emojis! Enjoy well-known casino games directly in your telegram app!\n\n"

        )
        
        active_menus[query.message.message_id] = user_id

        
        keyboard = [
            [InlineKeyboardButton("🆕🚀 Climber", callback_data='play_climber')],  # Full width button
            [InlineKeyboardButton("⚡️ Limbo", callback_data='play_limbo')],      # Full width button
            [InlineKeyboardButton("♠️ Hilo", callback_data='play_hilo'),
             InlineKeyboardButton("💣 Mines", callback_data='play_mines')],
            [InlineKeyboardButton("🔙", callback_data='games')]
        ]
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

        
    
        
    elif query.data == 'deposit':
        text = (
            "<b>Deposit - no minimum amount</b>\n\n"
            "Deposits are credited as soon as 1 blockchain confirmation is reached.\n\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎁 Deposit Telegram Gifts", callback_data='deposit_gifts')],
            [InlineKeyboardButton("Bitcoin (BTC)", callback_data='deposit_btc'),
             InlineKeyboardButton("Litecoin (LTC)", callback_data='deposit_ltc')],
            [InlineKeyboardButton("Dogecoin (DOGE)", callback_data='deposit_doge'),
             InlineKeyboardButton("Ethereum (ETH)", callback_data='deposit_eth')],
            [InlineKeyboardButton("Tron (TRX)", callback_data='deposit_trx'),
             InlineKeyboardButton("BNB (BNB)", callback_data='deposit_bnb')],
            [InlineKeyboardButton("Ripple (XRP)", callback_data='deposit_xrp'),
             InlineKeyboardButton("Polygon (POL)", callback_data='deposit_pol')],
            [InlineKeyboardButton("Ethereum (BASE)", callback_data='deposit_base'),
             InlineKeyboardButton("Solana (SOL)", callback_data='deposit_sol')],
            [InlineKeyboardButton("Toncoin (TON)", callback_data='deposit_ton'),
             InlineKeyboardButton("Monero (XMR)", callback_data='deposit_xmr')],
            [InlineKeyboardButton("USDT (TON)", callback_data='deposit_usdt_ton'),
             InlineKeyboardButton("USDT (TRC20)", callback_data='deposit_usdt_trc20')],
            [InlineKeyboardButton("USDT (ERC20)", callback_data='deposit_usdt_erc20'),
             InlineKeyboardButton("USDC (ERC20)", callback_data='deposit_usdc_erc20')],
            [InlineKeyboardButton("USDT (BEP20)", callback_data='deposit_usdt_bep20'),
             InlineKeyboardButton("USDC (BEP20)", callback_data='deposit_usdc_bep20')],
            [InlineKeyboardButton("USDC (BASE)", callback_data='deposit_usdc_base'),
             InlineKeyboardButton("USDT (SOL)", callback_data='deposit_usdt_sol')],
            [InlineKeyboardButton("USDC (SOL)", callback_data='deposit_usdc_sol'),
             InlineKeyboardButton("TRUMP (SOL)", callback_data='deposit_trump_sol')],
            [InlineKeyboardButton("USDT (POL)", callback_data='deposit_usdt_pol'),
             InlineKeyboardButton("USDC (POL)", callback_data='deposit_usdc_pol')],
            [InlineKeyboardButton(" Apple Pay", callback_data='deposit_applepay'),
             InlineKeyboardButton("🅿️ PayPal", callback_data='deposit_paypal')],
            [InlineKeyboardButton("®️ Revolut", callback_data='deposit_revolut'),
             InlineKeyboardButton("w Wise", callback_data='deposit_wise')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
        ]
        
        
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

        
    elif query.data == 'deposit_btc':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['btc'])
        address_sessions[user_id] = {'btc': (address, datetime.utcnow())}

        expires_in = "1 day, 0:00:00"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"

        # Check if it's private
        is_private = getattr(getattr(query.message, 'chat', None), 'type', '') == 'private'

        text = f"""<b>Deposit Bitcoin (BTC)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {expires_in}"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_btc')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )



        active_menus[query.message.message_id] = user_id


    elif query.data == 'refresh_btc':
        user_id = query.from_user.id
        address_data = address_sessions.get(user_id, {}).get('btc')

        if not address_data:
            await query.answer("Session expired.")
            return

        address, issued_at = address_data
        remaining = (issued_at + timedelta(days=1)) - datetime.utcnow()

        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This BTC deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        is_private = getattr(getattr(query.message, 'chat', None), 'type', '') == 'private'

        text = f"""<b>Deposit Bitcoin (BTC)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        # Only show the QR code on refresh in private chat
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_btc')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id


    elif query.data == 'deposit_ltc':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['ltc'])
        address_sessions[user_id] = {'ltc': (address, datetime.utcnow())}

        expires_in = "1 day, 0:00:00"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        is_private = getattr(getattr(query.message, 'chat', None), 'type', '') == 'private'

        text = f"""<b>Deposit Litecoin (LTC)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {expires_in}"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_ltc')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )


        active_menus[query.message.message_id] = user_id


    elif query.data == 'refresh_ltc':
        user_id = query.from_user.id
        address_data = address_sessions.get(user_id, {}).get('ltc')

        if not address_data:
            await query.answer("Session expired.")
            return

        address, issued_at = address_data
        remaining = (issued_at + timedelta(days=1)) - datetime.utcnow()

        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This LTC deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        is_private = getattr(query.message.chat, 'type', '') == 'private'

        text = f"""<b>Deposit Litecoin (LTC)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_ltc')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id

        
    elif query.data == 'deposit_usdc_base':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['usdc_base'])
        address_sessions[user_id] = {'usdc_base': (address, datetime.utcnow())}

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = False

            
        text = f"""
    <b>Deposit USDC (BASE)</b>\n
Deposit address: <code>{address}</code>

Address expires in 2:00:00

Accepted tokens: USDC (BASE)
    """


        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_usdc_base')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        
        active_menus[query.message.message_id] = user_id
        
    elif query.data == 'refresh_usdc_base':
        user_id = query.from_user.id
        address, issued_at = address_sessions.get(user_id, {}).get('usdc_base', (None, None))
        if not address:
            await query.answer("Session expired.")
            return

        remaining = (issued_at + timedelta(hours=2)) - datetime.utcnow()
        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This USDC deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = False

            
        text = f"""
    <b>Deposit USDC (BASE)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}\n
Accepted tokens: USDC (BASE)"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_usdc_base')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id
        
    elif query.data == 'deposit_usdc_erc20':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['usdc_erc'])
        address_sessions[user_id] = {'usdc_erc': (address, datetime.utcnow())}

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = True 

        text = f"""
    <b>Deposit USDC (ERC20)</b>\n
Deposit address: <code>{address}</code>

Address expires in 2:00:00

Accepted tokens: USDT (ERC20), USDC (ERC20)
    """

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_usdc_erc20')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )


        active_menus[query.message.message_id] = user_id

        
        
    elif query.data == 'refresh_usdc_erc20':
        user_id = query.from_user.id
        address_data = address_sessions.get(user_id, {}).get('usdc_erc')

        if not address_data:
            await query.answer("Session expired.")
            return

        address, issued_at = address_data
        remaining = (issued_at + timedelta(hours=2)) - datetime.utcnow()

        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This USDC (ERC20) deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = True 

        text = f"""
<b>Deposit USDC (ERC20)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}\n
Accepted tokens: USDT (ERC20), USDC (ERC20)"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data='refresh_usdc_erc20')],
                [InlineKeyboardButton("🔙 Back", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id




    elif query.data == 'deposit_usdc_bep20':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['usdc_bep'])
        address_sessions[user_id] = {'usdc_bep': (address, datetime.utcnow())}

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = True 

        text = f"""
    <b>Deposit USDC (BEP20)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in 2:00:00\n
Accepted tokens: USDT (BEP20), USDC (BEP20)"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_usdc_bep')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )


        active_menus[query.message.message_id] = user_id

    elif query.data == 'refresh_usdc_bep':
        user_id = query.from_user.id
        address_data = address_sessions.get(user_id, {}).get('usdc_bep')

        if not address_data:
            await query.answer("Session expired.")
            return

        address, issued_at = address_data
        remaining = (issued_at + timedelta(hours=2)) - datetime.utcnow()

        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This USDC (BEP20) deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = True 

        text = f"""
    <b>Deposit USDC (BEP20)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}\n
Accepted tokens: USDT (BEP20), USDC (BEP20)"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh", callback_data='refresh_usdc_bep')],
                [InlineKeyboardButton("🔙 Back", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id



        
    elif query.data == 'refresh_ltc':
        user_id = query.from_user.id
        address, issued_at = address_sessions.get(user_id, {}).get('ltc', (None, None))
        if not address:
            await query.answer("Session expired.")
            return

        remaining = (issued_at + timedelta(days=1)) - datetime.utcnow()
        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This LTC deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        try:
            is_private = query.message.chat.type == 'private'
        except AttributeError:
            is_private = False


        text = f"""
    <b>Deposit Litecoin (LTC)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}\n
"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_ltc')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )
        
        active_menus[query.message.message_id] = user_id


    elif query.data == 'deposit_eth':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['eth'])
        address_sessions[user_id] = {'eth': (address, datetime.utcnow())}

        chat_type = query.message.chat.type
        is_private = chat_type == 'private'

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        text = f"""
<b>Deposit Ethereum (ETH)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in 2:00:00\n
Accepted tokens: USDT (ERC20), USDC (ERC20)
        """

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_eth')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id


    elif query.data == 'refresh_eth':
        user_id = query.from_user.id
        address, issued_at = address_sessions.get(user_id, {}).get('eth', (None, None))
        if not address:
            await query.answer("Session expired.")
            return

        remaining = (issued_at + timedelta(hours=2)) - datetime.utcnow()
        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This ETH deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]

        chat_type = query.message.chat.type
        is_private = chat_type == 'private'

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"

        text = f"""
    <b>Deposit Ethereum (ETH)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}\n
Accepted tokens: USDT (ERC20), USDC (ERC20)
    """

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_eth')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id


    elif query.data == 'deposit_sol':
        user_id = query.from_user.id
        address = random.choice(CRYPTO_ADDRESSES['sol'])
        address_sessions[user_id] = {'sol': (address, datetime.utcnow())}

        chat_type = query.message.chat.type
        is_private = chat_type == 'private'

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"
        text = f"""
<b>Deposit Solana (SOL)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in 1:00:00\n
Accepted tokens: USDT (SOL), USDC (SOL)
        """

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        reply_markup = None
        if not getattr(query, '_from_command', False):
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_sol')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ])

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id


    elif query.data == 'refresh_sol':
        user_id = query.from_user.id
        address, issued_at = address_sessions.get(user_id, {}).get('sol', (None, None))
        if not address:
            await query.answer("Session expired.")
            return

        remaining = (issued_at + timedelta(hours=1)) - datetime.utcnow()
        if remaining.total_seconds() <= 0:
            await query.edit_message_text("This SOL deposit address has expired.")
            return

        remaining_str = str(remaining).split('.')[0]

        chat_type = query.message.chat.type
        is_private = chat_type == 'private'

        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={address}"

        text = f"""
    <b>Deposit Solana (SOL)</b>\n
Deposit address: <code>{address}</code>\n
Address expires in {remaining_str}\n
Accepted tokens: USDT (SOL), USDC (SOL)
"""

        if is_private:
            text += f'\n<a href="{qr_url}">\u200b</a>'

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄", callback_data='refresh_sol')],
                [InlineKeyboardButton("🔙", callback_data='deposit')]
            ]),
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        active_menus[query.message.message_id] = user_id


    elif query.data == 'back_to_main':
        # Zurück zum Hauptmenü
        keyboard = [
            [InlineKeyboardButton("🎁 Deposit gifts", callback_data='deposit_gifts')],
            [InlineKeyboardButton("🆕📈 Predictions", callback_data='predictions'),
             InlineKeyboardButton("🆕🚀 Crash", callback_data='crash')],
            [InlineKeyboardButton("👥 Join Group", url='https://t.me/DenaroCasinoChat')],
            [InlineKeyboardButton("🎱 Games", callback_data='games')],
            [InlineKeyboardButton("📥 Deposit", callback_data='deposit'),
             InlineKeyboardButton("📤 Withdraw", callback_data='withdraw')],
            [InlineKeyboardButton("💰 Refer and Earn", callback_data='refer')],
            [InlineKeyboardButton("⚙️ Settings", callback_data='settings')]
        ]
        await query.edit_message_text("Denaro Casino\n\nBalance: 0€", reply_markup=InlineKeyboardMarkup(keyboard))         
        
    elif query.data == 'withdraw':
        text = (
            "<b>Withdraw</b>\n\n"
            "There are 14 cryptocurrencies supported for withdrawals.\n\n"
            "Choose your favourite one!"
        )
        keyboard = [
            [InlineKeyboardButton("Bitcoin (BTC)", callback_data='withdraw_btc'),
             InlineKeyboardButton("Litecoin (LTC)", callback_data='withdraw_ltc')],
            [InlineKeyboardButton("Toncoin (TON)", callback_data='withdraw_ton'),
             InlineKeyboardButton("Ethereum (ETH)", callback_data='withdraw_eth')],
            [InlineKeyboardButton("USDT (ERC20)", callback_data='withdraw_usdt_erc20'),
             InlineKeyboardButton("USDC (ERC20)", callback_data='withdraw_usdc_erc20')],
            [InlineKeyboardButton("USDT (POL)", callback_data='withdraw_usdt_pol'),
             InlineKeyboardButton("USDC (POL)", callback_data='withdraw_usdc_pol')],
            [InlineKeyboardButton("Solana (SOL)", callback_data='withdraw_sol'),
             InlineKeyboardButton("Tron (TRX)", callback_data='withdraw_trx')],
            [InlineKeyboardButton("USDT (TRC20)", callback_data='withdraw_usdt_trc20'),
             InlineKeyboardButton("BNB (BEP20)", callback_data='withdraw_bnb_bep20')],
            [InlineKeyboardButton("USDT (BEP20)", callback_data='withdraw_usdt_bep20'),
             InlineKeyboardButton("Monero (XMR)", callback_data='withdraw_xmr')],
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id

    elif query.data in withdraw_coin_info:
        coin, fee, minimum = withdraw_coin_info[query.data]
        await handle_withdraw(query, context, coin, fee, minimum)


        
    elif query.data == 'refer':
        text = (
            "<b>Referral Program</b>\n\n"
            "Invite your friends to join the bot using referral link and earn money!\n\n"
            "<b>Benefits</b>\n\n"
            "- 1% of every deposit made by your referrals (1$ per 100$ deposited)\n"
            "- 20% of profit share\n"
            "- 10% of the PvP commission of your referrals (0.1$ per 100$ wagered)\n\n"
            "<b>Group owners additional advantages</b>\n\n"
            "- 40% of the dice PvP commission in your group (0.8$ per 100$ wagered)\n\n"
            "Referrals count: <b>0</b>\n\n"
            "Available funds: <b>0 kas</b>\n"
            "Withdrawn funds: <b>$0</b>\n\n"
            "Your bot referral link: <a href='https://t.me/DenaroCasinoBot?start=uutnuku'>https://t.me/DenaroCasinoBot?start=uutnuku</a>\n"
            "Your group referral link: <a href='https://t.me/+JdLEwjCQRqIzN2E0'>https://t.me/+JdLEwjCQRqIzN2E0</a>\n\n"
            "Both bot and group links will make anyone that clicks on them instantly your referral, "
            "if he was not already referred and did not deposit yet"
        )
        keyboard = [
            [InlineKeyboardButton("🔗 Share link", switch_inline_query="forward")],  # This triggers the forward action
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            disable_web_page_preview=True  # This disables the link preview (popup)
        )
        
        active_menus[query.message.message_id] = user_id

        
    elif query.data == 'settings':
        text = (
            "<b>⚙️ Settings</b>\n\n"
        )
        keyboard = [
            [
                InlineKeyboardButton("💱 Currency", callback_data='currency'),  # Button for Currency
                InlineKeyboardButton("❌ Privacy", callback_data='privacy')   # Button for Privacy
            ],
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]  # Back button to the main menu
        ]
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        active_menus[query.message.message_id] = user_id
        
    elif query.data == 'play_dart':
        user_id = query.from_user.id
        message_id = query.message.message_id

        # Schutz gegen fremde Klicks
        if message_id in active_menus and active_menus[message_id] != user_id:
            await query.answer()  # still block
            return

        text = (
            "<b>Choose amount</b>\n\n"
            "How much are you going to bet in this match?\n\n"
        )
        keyboard = [
            [InlineKeyboardButton("Play", callback_data='play_dart')]
        ]

        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

        # Optional: Update Zuordnung, falls Menü aktualisiert wird
        active_menus[message_id] = user_id


    elif query.data == 'privacy':
        # Get or initialize privacy state
        user_id = query.from_user.id
        privacy_enabled[user_id] = not privacy_enabled.get(user_id, False)
        
        # Prepare the response
        new_text = "✅ Privacy" if privacy_enabled[user_id] else "❌ Privacy"
        status_text = "Privacy mode is now enabled" if privacy_enabled[user_id] else "Privacy mode is now disabled"
        
        # First answer the callback query with the popup
        try:
            await context.bot.answer_callback_query(
                callback_query_id=query.id,
                text=status_text,
                show_alert=True
            )
        except Exception as e:
            print(f"Error showing popup: {e}")
        
        # Then update the message
        keyboard = [
            [InlineKeyboardButton("💱 Currency", callback_data='currency'),
             InlineKeyboardButton(new_text, callback_data='privacy')],
            [InlineKeyboardButton("🔙", callback_data='back_to_main')]
        ]
        
        try:
            await query.edit_message_text(
                text="<b>⚙️ Settings</b>\n\n",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            
           





# Bot starten
if __name__ == '__main__':
    app = ApplicationBuilder().token("7509137727:AAH99SgDSAof_RXg5n1eTgEOLS1pXrXYNms").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["depo", "deposit"], depo))
    app.add_handler(CommandHandler("dice", dice))
#    app.add_handler(CallbackQueryHandler(choose_game_mode, pattern='game_'))
    app.add_handler(CallbackQueryHandler(play_dice, pattern='play_dice'))
#  app.add_handler(CallbackQueryHandler(choose_game_mode, pattern=r'^(game_|first_to_|rolls_).*'))
    app.add_handler(CommandHandler(["housebalance", "hb"], house_balance))
    app.add_handler(CommandHandler("darts", darts))
    app.add_handler(CallbackQueryHandler(play_dart, pattern="^play_dart$"))
    app.add_handler(CommandHandler(["bal", "balance"], show_balance))
    app.add_handler(CommandHandler("mypreds", mypreds))
    app.add_handler(CommandHandler(["maxbet", "maxbets"], maxbet))
    app.add_handler(CommandHandler(["side", "sides"], sides))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler(["level", "levels"], levels))
    app.add_handler(CommandHandler("tip", tip_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, detect_group_add))
    app.post_init = on_startup

    app.run_polling()
