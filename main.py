from functions import main_menu, high_scores, single_player, battle, options


cont = True
while cont:
    cont, index = main_menu()
    if index == 0:
        cont = single_player()
    elif index == 1:
        end = battle()
        cont = not end
    elif index == 2:
        cont = high_scores()
    elif index == 3:
        cont = options()
    else:
        cont = False
quit()
