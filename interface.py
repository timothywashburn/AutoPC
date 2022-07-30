import torch
from main import PriceCheckNetwork
from main import column_num
from main import device
from main import no_lives
from utils import colored

from enchantMap import enchants as enchantMap

model = PriceCheckNetwork().to(device)
state_dict = torch.load("trained-network.pth")
model.load_state_dict(state_dict)
model.eval()


class LivesGreaterThanMaxLivesError(ValueError):
    pass


nth = ["first", "second", "third"]
while True:
    enchants = []
    lives = None
    max_lives = None
    gemmed = False

    for i in range(3):
        break_loop = False
        while True:
            user_input = input(colored(200, 200, 200, "Input") + colored(255, 188, 79, nth[i]) +
                          colored(200, 200, 200, "enchant & level (or \"none\"):"))
            args = user_input.split(" ")
            if len(args) == 0:
                print(colored(200, 200, 200, "You must have both an enchant and a level (ex: \"bill 3\")"))
                continue

            enchant = args[0]
            if enchant.casefold() == "none" and i > 0:
                break_loop = True
                break
            elif len(args) != 2:
                print(colored(200, 200, 200, "You must have both an enchant and a level (ex: \"bill 3\")"))
                continue

            enchant_key = None
            should_restart = False
            for key in enchantMap.keys():
                if enchant.casefold() not in enchantMap[key]["refs"]:
                    continue
                for enchant_and_level in enchants:
                    if list(enchant_and_level.keys())[0].casefold() == key:
                        print(colored(200, 200, 200, "Enchant already added"))
                        should_restart = True
                        break
                if should_restart:
                    break
                enchant_key = key
            if should_restart:
                continue
            if enchant_key is None:
                print(colored(200, 200, 200, "That enchant does not exist"))
                continue

            level = None
            try:
                level = int(args[1])
                if level < 1 or level > 3:
                    raise ValueError()
            except ValueError:
                print(colored(200, 200, 200, "Level must be a number between 1 and 3"))
                continue

            enchants.append({enchant_key: level})
            break
        if break_loop:
            break

    if not no_lives:
        while True:
            user_input = input(colored(200, 200, 200, "Input lives (lives/max):"))

            args = user_input.split("/")
            if len(args) != 2:
                print(colored(200, 200, 200, "Invalid format (ex: \"20/20\")"))
                continue

            lives = None
            try:
                lives = int(args[0])
                if lives < 0:
                    raise ValueError()
            except ValueError:
                print(colored(200, 200, 200, "Invalid amount of lives"))
                continue

            max_lives = None
            try:
                max_lives = int(args[1])
                if max_lives < 0 or max_lives > 100:
                    raise ValueError()
                if lives > max_lives:
                    raise LivesGreaterThanMaxLivesError()
            except LivesGreaterThanMaxLivesError:
                print(colored(200, 200, 200, "Lives cannot be higher than max lives"))
                continue
            except ValueError:
                print(colored(200, 200, 200, "Invalid amount of max lives"))
                continue
            break

    while True:
        user_input = input(colored(200, 200, 200, "Gemmed? (yes/no):"))
        if "y" in user_input.casefold():
            gemmed = True
            break
        elif "n" in user_input.casefold():
            break
        else:
            print(colored(200, 200, 200, "Could not understand"))
            continue

    with torch.no_grad():
        all_enchant_levels = []
        for enchant in enchantMap:
            should_add = False
            level = None
            for enchant_and_level in enchants:
                if enchant != list(enchant_and_level.keys())[0]:
                    continue
                should_add = True
                level = list(enchant_and_level.values())[0]
                break
            all_enchant_levels.append(level if should_add else 0)
        item_data = [lives, max_lives, 1 if gemmed else 0, *all_enchant_levels]
        if no_lives:
            item_data = item_data[2:]
        prediction = model.forward(torch.FloatTensor(item_data).view(1, column_num).to(device))
        print(colored(200, 200, 200, "Estimated Worth:") + colored(215, 180, 243, round(prediction.item(), 1)) +
              colored(215, 180, 243, "PB" + ("s" if prediction.item() != 1 else "")))
    print("")
