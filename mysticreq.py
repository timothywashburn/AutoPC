import requests
import nbt
import io
import base64
from enchantMap import enchants as enchantMap
from csv import writer
import os.path
import sys
from utils import colored

items = []


def get_items():
    global items
    items = []
    players = requests.get("https://pitpanda.rocks/api/randomplayers").json()["players"]
    count = 0
    print("")
    for player in players:
        if count >= 3:
            break
        count += 1

        player_data = requests.get("https://pitpanda.rocks/api/chattriggers/" + player["uuid"]).json()["data"]
        print("Loading data from: " + player_data["name"])
        inventories = [player_data["nbtInventories"]["inventory"], player_data["nbtInventories"]["enderchest"],
                       player_data["nbtInventories"]["armor"]]
        for inventory in inventories:
            data = nbt.nbt.NBTFile(fileobj=io.BytesIO(base64.b64decode(inventory)))
            for item in data["i"]:
                try:
                    if item["id"].value != 283:
                        continue
                except KeyError:
                    continue
                items.append(item)


headers = ["Price", "Lives", "Max Lives", "Gemmed?"]
for key in enchantMap:
    headers.append(enchantMap[key]["display"].title())

while True:
    get_items()
    for item in items:
        attributes, enchantNBT = None, None
        try:
            attributes = item["tag"]["ExtraAttributes"]
            enchantNBT = attributes["CustomEnchants"]
        except KeyError:
            continue

        tier = attributes["UpgradeTier"].value
        if tier != 3:
            continue

        lives = attributes["Lives"].value
        maxLives = attributes["MaxLives"].value
        gemmed = 0
        try:
            gemmed = attributes["UpgradeGemsUses"].value
        except KeyError:
            pass
        enchants = []

        for enchant in enchantNBT:
            enchants.append({
                enchant["Key"].value: enchant["Level"].value
            })

        print("")
        print(colored(200, 79 if lives <= 7 else 200, 79 if lives <= 7 else 200, f"Lives: {lives}/{maxLives}"))
        print(colored(200, 200, 200, f"Gemmed: ") + (colored(100, 255, 100, "Yes") if gemmed else colored(200, 200, 200, "No")))
        names_and_levels = {}
        for enchant in enchants:
            name = enchantMap[list(enchant.keys())[0]]["display"].title()
            level = list(enchant.values())[0]
            names_and_levels[name] = level
            print(colored(255, 188, 79, f"{name}: {level}"))

        price = None
        while True:
            price = input(colored(200, 200, 200, "input price in PBs: "))
            if price.lower() == "skip":
                print("\nskipping")
                price = None
                break
            elif price.lower() == "quit" or price.lower() == "exit":
                print("\nexiting")
                sys.exit(0)
            try:
                price = float(price)
                break
            except ValueError:
                print("Invalid price")
        if price is None:
            continue

        insert_row = [price, lives, maxLives, gemmed]
        for key in enchantMap:
            if enchantMap[key]["display"].title() in names_and_levels.keys():
                insert_row.append(names_and_levels[enchantMap[key]["display"].title()])
            else:
                insert_row.append(0)

        file_exists = os.path.isfile("output.csv")
        with open("output.csv", "a", newline="") as f_object:
            writer_object = writer(f_object)

            if not file_exists or os.stat("output.csv").st_size == 0:
                writer_object.writerow(headers)

            writer_object.writerow(insert_row)
            f_object.close()