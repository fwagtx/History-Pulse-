# =============================================================================
#  BAD TYCOON - Part 1: Money and Income
# =============================================================================
#  What this does:
#    - Every player gets their own money balance
#    - Money goes up automatically every few seconds (passive income)
#    - A button lets a player spend money to increase their income rate
#
#  That tiny loop - earn, spend, earn faster - IS the tycoon genre. Everything
#  else we add later is decoration on top of it.
#
#  HOW TO READ VERSE (you said you're new, so):
#    - Lines starting with # are comments. The game ignores them.
#    - Indentation matters. Code indented under a line belongs to that line.
#    - `:=` means "define this". `=` means "set this to".
#    - `var` means a value that can change later. Without it, it's fixed.
# =============================================================================

# These give us access to Epic's built-in code. Always needed at the top.
using { /Fortnite.com/Devices }
using { /Verse.org/Simulation }
using { /UnrealEngine.com/Temporary/Diagnostics }

# This creates a new device you can place in your map, like any Epic device.
# `creative_device` means "this is a placeable device".
bad_tycoon_core := class(creative_device):

    # -------------------------------------------------------------------------
    # SETTINGS - @editable means you can change these in UEFN without touching
    # code. Click the device in your map and they appear in the Details panel.
    # -------------------------------------------------------------------------

    # Drag your button device onto this slot in UEFN.
    @editable
    UpgradeButton : button_device = button_device{}

    # Optional feedback. A HUD Message device holds ONE fixed message, typed into
    # its Details panel in UEFN - you can't send text to it from code. So we use
    # two: set one to "Upgrade bought!" and the other to "Not enough money".
    @editable
    BoughtMessage : hud_message_device = hud_message_device{}

    @editable
    TooPoorMessage : hud_message_device = hud_message_device{}

    # How much money players start with.
    @editable
    StartingMoney : int = 0

    # How many seconds between each payout.
    @editable
    TickSeconds : float = 2.0

    # How much the upgrade costs.
    @editable
    UpgradeCost : int = 25

    # How much each upgrade adds to income per tick.
    @editable
    UpgradeBonus : int = 1

    # -------------------------------------------------------------------------
    # MEMORY - these store each player's progress while the game runs.
    # `[player]int` means "for each player, remember a whole number".
    # -------------------------------------------------------------------------

    var PlayerMoney : [player]int = map{}
    var PlayerIncome : [player]int = map{}

    # -------------------------------------------------------------------------
    # STARTUP - OnBegin runs once automatically when the map starts.
    # -------------------------------------------------------------------------

    OnBegin<override>()<suspends> : void =

        # When someone presses the button, run our OnUpgradePressed function.
        UpgradeButton.InteractedWithEvent.Subscribe(OnUpgradePressed)

        # Set up everyone already in the game.
        for (P : GetPlayspace().GetPlayers()):
            SetupPlayer(P)

        # Also set up anyone who joins later.
        GetPlayspace().PlayerAddedEvent().Subscribe(OnPlayerJoined)

        # `spawn` starts the income loop running in the background, so it keeps
        # paying players out while the rest of the map carries on.
        spawn{IncomeLoop()}

        Print("BAD Tycoon started")

    OnPlayerJoined(P : player) : void =
        SetupPlayer(P)

    # Give a player their starting values.
    SetupPlayer(P : player) : void =
        # Note: `set Map[Key] = Value` can fail in Verse (the key might not fit),
        # so it's wrapped in `if (...) {}` - that means "try it, carry on either way".
        # If the compiler complains here, tell me and I'll switch it to the plain form.
        if (set PlayerMoney[P] = StartingMoney) {}
        if (set PlayerIncome[P] = 1) {}

    # -------------------------------------------------------------------------
    # INCOME LOOP - runs forever, paying every player every few seconds.
    # `<suspends>` marks a function that can pause (because of Sleep).
    # -------------------------------------------------------------------------

    IncomeLoop()<suspends> : void =
        loop:
            Sleep(TickSeconds)
            for (P : GetPlayspace().GetPlayers()):
                PayPlayer(P)

    PayPlayer(P : player) : void =
        # Read both values. If either is missing, this whole block is skipped.
        if (Income := PlayerIncome[P], Money := PlayerMoney[P]):
            if (set PlayerMoney[P] = Money + Income) {}

    # -------------------------------------------------------------------------
    # THE UPGRADE BUTTON
    # `agent` is Verse's general word for "someone in the game". We convert it
    # to a `player` because our money map is keyed by player.
    # -------------------------------------------------------------------------

    OnUpgradePressed(Agent : agent) : void =
        if (P := player[Agent]):
            if (Money := PlayerMoney[P], Income := PlayerIncome[P]):

                # Can they afford it? `>=` here succeeds or fails, which is how
                # Verse does conditions.
                if (Money >= UpgradeCost):
                    if (set PlayerMoney[P] = Money - UpgradeCost) {}
                    if (set PlayerIncome[P] = Income + UpgradeBonus) {}
                    BoughtMessage.Show(P)
                    Print("Upgrade purchased")
                else:
                    TooPoorMessage.Show(P)
