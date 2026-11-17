"""Text for the add-on in English and Russian: entity and item names, interaction prompts and every message the
script shows. The script sends `rawtext` translate keys, so each player reads the game in their own language.

Film quotes stay in English in both languages: they are the film's lines.
"""

ENTITIES = {  # id: (English, Russian, English spawn egg, Russian spawn egg)
    "cyclops": ("Polyphemus", "Полифем"),
    "laestrygonian": ("Laestrygonian", "Лестригон"),
    "laestrygonian_child": ("Laestrygonian Child", "Лестригонский ребёнок"),
    "circe": ("Circe", "Цирцея"),
    "circe_sister": ("Circe's Sister", "Сестра Цирцеи"),
    "siren": ("Siren", "Сирена"),
    "scylla": ("Scylla", "Скилла"),
    "charybdis": ("Charybdis", "Харибда"),
    "shade": ("Shade", "Тень"),
    "tiresias": ("Tiresias", "Тиресий"),
    "sun_cattle": ("Cattle of Apollo", "Бык Аполлона"),
    "calypso": ("Calypso", "Калипсо"),
    "athena": ("Athena", "Афина"),
    "trojan_horse": ("Trojan Horse", "Троянский конь"),
    "boulder": ("Boulder", "Валун"),
}
NO_EGG = {"boulder", "circe_sister"}

ITEMS = {"beeswax": ("Wax", "Воск"), "burning_stake": ("Burning Stake", "Горящий кол"),
         "circe_stew": ("Circe's Stew", "Похлёбка Цирцеи"), "lotus_flower": ("Lotus Flower", "Цветок лотоса")}

ACTIONS = {
    "stew": ("Beg for Food", "Просить еды"), "counsel": ("Ask the Way Home", "Спросить дорогу домой"),
    "seize": ("Seize Her Sister", "Схватить её сестру"), "lotus": ("Accept a Lotus", "Принять лотос"),
    "embrace": ("Embrace", "Обнять"), "athena": ("Speak with Athena", "Говорить с Афиной"),
    "hide": ("Hide Inside", "Спрятаться внутри"),
}

# key: (English, Russian). Colour codes are kept in both.
MESSAGES = {
    # ---- the journey
    "odyssey.title": ("THE ODYSSEY", "ОДИССЕЯ"),
    "odyssey.subtitle": ("Sail home, if you can.", "Плыви домой, если сможешь."),
    "odyssey.kit": ("§7You are given the crew's supplies: boats, wax and a burning stake.",
                    "§7Вы получили припасы команды: лодки, воск и горящий кол."),
    "odyssey.site.ogygia": ("OGYGIA", "ОГИГИЯ"), "odyssey.site.ogygia.sub": ("The island of Calypso", "Остров Калипсо"),
    "odyssey.site.cyclops": ("THE CYCLOPS", "ЦИКЛОП"), "odyssey.site.cyclops.sub": ("The island of Polyphemus", "Остров Полифема"),
    "odyssey.site.telepylus": ("TELEPYLUS", "ТЕЛЕПИЛ"), "odyssey.site.telepylus.sub": ("The land of the Laestrygonians", "Земля лестригонов"),
    "odyssey.site.aeaea": ("AEAEA", "ЭЯ"), "odyssey.site.aeaea.sub": ("The island of Circe", "Остров Цирцеи"),
    "odyssey.site.hades": ("HADES", "АИД"), "odyssey.site.hades.sub": ("Beyond the river Oceanus", "За рекой Океан"),
    "odyssey.site.sirens": ("THE SIRENS", "СИРЕНЫ"), "odyssey.site.sirens.sub": ("Do not listen", "Не слушай"),
    "odyssey.site.strait": ("SCYLLA AND CHARYBDIS", "СКИЛЛА И ХАРИБДА"),
    "odyssey.site.strait.sub": ("Six lives, or all of them", "Шесть жизней или все"),
    "odyssey.site.thrinacia": ("THRINACIA", "ТРИНАКИЯ"), "odyssey.site.thrinacia.sub": ("The cattle of Apollo", "Быки Аполлона"),
    "odyssey.site.ithaca": ("ITHACA", "ИТАКА"), "odyssey.site.ithaca.sub": ("Home", "Дом"),
    "odyssey.site.troy": ("TROY", "ТРОЯ"), "odyssey.site.troy.sub": ("The horse on the beach", "Конь на берегу"),
    # ---- Polyphemus
    "odyssey.cy.cry": ("§bPolyphemus: §f\"Father Poseidon, they blinded me! Vengeance, father, vengeance for pain... Poseidon, vengeance for pain!\"",
                       "§bПолифем: §f\"Father Poseidon, they blinded me! Vengeance, father, vengeance for pain... Poseidon, vengeance for pain!\""),
    "odyssey.cy.blind_hint": ("§7He is blind. He counts his sheep by feeling their wool — hide among the flock.",
                              "§7Он ослеплён. Он считает овец, ощупывая шерсть, — спрячьтесь в стаде."),
    "odyssey.cy.hidden": ("§7Polyphemus runs his hands over the wool of his sheep... he does not find you.",
                          "§7Полифем водит руками по шерсти овец... он вас не находит."),
    "odyssey.cy.devour": ("§4Polyphemus snatches you up and lifts you to his mouth...",
                          "§4Полифем хватает вас и подносит ко рту..."),
    "odyssey.cy.kick": ("§cA kick from Polyphemus sends you flying.", "§cПинок Полифема отбрасывает вас."),
    "odyssey.cy.stomp": ("§cThe ground shakes under Polyphemus's foot.", "§cЗемля содрогается под ногой Полифема."),
    # ---- Laestrygonians
    "odyssey.lae.child_laugh": ("§7You ask the armoured child for hospitality. The child only laughs at you.",
                                "§7Вы просите у ребёнка в доспехах гостеприимства. Он лишь смеётся над вами."),
    "odyssey.lae.child_scream": ("§7You ask again, more seriously. §cThe child screams and runs. Something enormous moves in the fog...",
                                 "§7Вы просите снова, уже серьёзно. §cРебёнок кричит и убегает. В тумане движется нечто огромное..."),
    "odyssey.lae.emerge": ("§7Giants in silver armour emerge from the fog.", "§7Из тумана выходят великаны в серебряных доспехах."),
    "odyssey.lae.impale": ("§cThe glaive lifts you off your feet and flings you into the air.",
                           "§cГлефа поднимает вас и швыряет в воздух."),
    "odyssey.lae.crush": ("§cThe mace crushes the ground beneath you.", "§cБулава сокрушает землю под вами."),
    # ---- Circe
    "odyssey.circe.scream": ("§5Circe screams at the sight of armoured strangers.", "§5Цирцея кричит, увидев чужаков в доспехах."),
    "odyssey.circe.no_armor": ("§5Circe will feed you — on condition that you leave your armour outside.",
                               "§5Цирцея накормит вас — если вы оставите доспехи снаружи."),
    "odyssey.circe.stew": ("§5Circe sets a bowl of stew before you.", "§5Цирцея ставит перед вами миску похлёбки."),
    "odyssey.circe.pliable": ("§dYou devour the stew with a grotesque hunger... and feel strangely pliable.",
                              "§dВы с жадностью поглощаете похлёбку... и чувствуете странную податливость."),
    "odyssey.circe.molded": ("§5Circe works your flesh and bones as a potter works clay. Your scream becomes a squeal.",
                             "§5Цирцея мнёт вашу плоть и кости, как гончар глину. Ваш крик превращается в визг."),
    "odyssey.circe.human": ("§aYou are human again.", "§aВы снова человек."),
    "odyssey.circe.seized": ("§5You grab Circe's sister. Circe stands down.", "§5Вы хватаете сестру Цирцеи. Цирцея отступает."),
    "odyssey.circe.claims": ("§5Circe says she only made your men what they really are — brutal and savage. Reluctantly, she turns them back.",
                             "§5Цирцея говорит, что лишь сделала ваших людей теми, кто они есть, — жестокими и дикими. Неохотно она возвращает им облик."),
    "odyssey.circe.hades": ("§5To reach Ithaca, she tells you, you must cross the river Oceanus into Hades.",
                            "§5Чтобы добраться до Итаки, говорит она, нужно пересечь реку Океан и войти в Аид."),
    "odyssey.circe.counsel": ("§5Circe: to reach Ithaca, you must cross the river Oceanus into Hades.",
                              "§5Цирцея: чтобы добраться до Итаки, нужно пересечь реку Океан и войти в Аид."),
    # ---- the Sirens
    "odyssey.siren.muffled": ("§7Wax in your ears: the song is only a muffled hum.", "§7Воск в ушах: песня — лишь глухое гудение."),
    "odyssey.siren.mast": ("§5Bound to the mast, you hear it all: everything you could ever want — and why you can never have it.",
                           "§5Привязанный к мачте, вы слышите всё: всё, чего вы могли бы желать, и почему этого никогда не получить."),
    "odyssey.siren.pull": ("§d♪ The Sirens' song draws you toward the rocks... ♪", "§d♪ Песня сирен влечёт вас к скалам... ♪"),
    "odyssey.siren.dragged": ("§4The Sirens drag you under.", "§4Сирены тянут вас на дно."),
    "odyssey.siren.wax_on": ("§eYou press soft wax into your ears. The sound dulls away.",
                             "§eВы вдавливаете мягкий воск в уши. Звук стихает."),
    "odyssey.siren.wax_off": ("§eThe wax has worked loose. You can hear again.", "§eВоск выпал. Вы снова слышите."),
    # ---- Scylla and Charybdis
    "odyssey.scylla.snatch": ("§4Scylla's heads lunge out of the cliff and snatch their victims from the deck.",
                              "§4Головы Скиллы вырываются из скалы и хватают жертв с палубы."),
    "odyssey.scylla.devour": ("§4A head of Scylla hauls you up toward the cliff and chews.",
                              "§4Голова Скиллы тянет вас вверх к утёсу и жуёт."),
    "odyssey.scylla.rend": ("§4Scylla tears through the ship.", "§4Скилла разрывает корабль."),
    "odyssey.charybdis.drain": ("§3The sea is draining into Charybdis's throat!", "§3Море уходит в глотку Харибды!"),
    "odyssey.charybdis.surge": ("§3The whirlpool surges!", "§3Водоворот набирает силу!"),
    # ---- Hades
    "odyssey.hades.rise": ("§7The blood soaks into the black sand. The dead begin to rise.",
                           "§7Кровь впитывается в чёрный песок. Мёртвые начинают подниматься."),
    "odyssey.hades.sinon": ("§7Sinon's shade reproaches you for deceiving him — and reveals that Antinous manipulated him into taking his place in the Greek army.",
                            "§7Тень Синона упрекает вас в обмане — и сообщает, что Антиной принудил его занять своё место в греческом войске."),
    "odyssey.hades.agamemnon": ("§7Agamemnon's shade reveals that Clytemnestra murdered him on his return, in revenge for sacrificing their daughter Iphigenia to Artemis for fair seas.",
                                "§7Тень Агамемнона сообщает, что Клитемнестра убила его по возвращении, мстя за жертвоприношение их дочери Ифигении ради попутных ветров."),
    "odyssey.hades.tiresias": ("§fTiresias: \"The Whirlpool in the sea takes all of your lives, the monster in the cliff only six.\"",
                               "§fТиресий: \"The Whirlpool in the sea takes all of your lives, the monster in the cliff only six.\""),
    "odyssey.hades.fate": ("§7Tiresias foretells that, by divine will, only you will return home — and that your men will die if they kill the cattle of Apollo.",
                           "§7Тиресий предрекает, что волею богов домой вернётесь лишь вы — и что ваши люди погибнут, если убьют быков Аполлона."),
    "odyssey.hades.crew": ("§cThe shades rapidly approaching are your unburied crew. They want you to join them in their shame.",
                           "§cСтремительно приближающиеся тени — ваша непогребённая команда. Они хотят, чтобы вы разделили их позор."),
    "odyssey.hades.grasp": ("§cThe dead drag at you, wanting you to join them.", "§cМёртвые тянут вас к себе, желая, чтобы вы стали одним из них."),
    # ---- the gods and Ogygia
    "odyssey.zeus.storm": ("§6You have killed one of the cattle of Apollo. Zeus sends a storm.",
                           "§6Вы убили одного из быков Аполлона. Зевс посылает бурю."),
    "odyssey.calypso.lotus": ("§bCalypso offers you a lotus flower.", "§bКалипсо предлагает вам цветок лотоса."),
    "odyssey.calypso.eaten": ("§bA peaceful haze settles over you. Your memories slip away.",
                              "§bВас окутывает мирная дымка. Воспоминания ускользают."),
    "odyssey.calypso.embrace": ("§bCalypso holds you close. For a moment you are at ease.",
                                "§bКалипсо обнимает вас. На мгновение вам спокойно."),
    "odyssey.athena.bless": ("§fAthena commands you to return home. You feel her protection settle over you.",
                             "§fАфина велит вам вернуться домой. Вы чувствуете её защиту."),
    "odyssey.athena.vision": ("§fAthena appears in your hour of crisis: \"Return home.\"",
                              "§fАфина является в час вашей беды: «Возвращайся домой.»"),
    "odyssey.horse.hide": ("§7You hide inside the Trojan Horse.", "§7Вы прячетесь внутри Троянского коня."),
    "odyssey.horse.sally": ("§7The Greeks pour out of the horse.", "§7Греки выходят из коня."),
}


def texts(language):
    """All lang lines for a language ('en_US' or 'ru_RU') as (key, value) pairs."""
    i = 0 if language == "en_US" else 1
    out = []
    for eid, names in ENTITIES.items():
        out.append((f"entity.studio:{eid}.name", names[i]))
    for eid, names in ENTITIES.items():
        if eid in NO_EGG:
            continue
        out.append((f"item.spawn_egg.entity.studio:{eid}.name", ("Spawn " if i == 0 else "Призвать: ") + names[i]))
    for iid, names in ITEMS.items():
        out.append((f"item.studio:{iid}.name", names[i]))
    for aid, names in ACTIONS.items():
        out.append((f"action.interact.studio.{aid}", names[i]))
    for key, pair in MESSAGES.items():
        out.append((key, pair[i]))
    return out
