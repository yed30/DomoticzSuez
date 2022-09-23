
# Domoticz Plugin Suez ToutSurMonEau
Voir le chapitre [Pour les francophones](#Pour les francophones) ci-dessous pour une description en français.

## For English speaking users
### Description

[Domoticz](https://domoticz.com) plugin that grabs data from French water meter. It grabs data from [toutsurmoneau](https://www.toutsurmoneau.fr) user account and store them inside a counter device log.
This is a fork of the [DomoticzSuez](https://github.com/Markourai/DomoticzSuez)


### Installing

Copy the plugin.py to domoticz directory/plugins/DomoticzSuez or change directory to domoticz directory/plugins and issue the following command:

```
git clone https://github.com/yed30/DomoticzSuez
```

To update, overwrite plugin.py or change directory to domoticz directory/plugins/DomoticzLinky and issue the following command:
```
git pull
```

Give the execution permission, for Linux:
```
chmod ugo+x plugin.py
```

Restart Domoticz.

### Configuration

Add the Suez hardware in Domoticz Settings / Hardware configuration tab, giving the e-mail address and password of your toutsurmoneau account. You can choose the number of days to collect data for the days log, something around 5 should do the trick. Just put more days once if you want to recover old history from website. Please note that when testing I couldn't recover more than 800 days. If you have un exception, please lower the number of days and retest.

After enabling the hardware, you shall have a new Suez Utility device and watch your energy consumption history with the Log button.

### Migrating from Markourai plugin
***Please ensure you backup your database before migrating.***
Stop Domoticz, and either remove directory/plugins/DomoticzSuez and then proceed with the installation step
Or, if you used git, issue the following commands
```
git remote set-url origin https://github.com/yed30/DomoticzSuez
git pull

```
Then restart Domoticz. 

You can change the number of days to collect the missing history using the Days field.

## Pour les francophones
### Description

Ce plugin [Domoticz](https://domoticz.com) récupère les données de consommation d'eau du site de Suez [toutsurmoneau](https://www.toutsurmoneau.fr), en utilisant le compte utilisateur, et les stocke dans un dispositif Domoticz.
Ce repo git est un fork de [DomoticzSuez](https://github.com/Markourai/DomoticzSuez)


### Installation

Copier le fichier plugin.py dans le répertoire domoticz plugins/DomoticzSuez ou se positionner dans le répertoire domoticz directory/plugins et exécuter la commande suivante:

```
git clone https://github.com/yed30/DomoticzSuez
```

Pour mettre à jour le fichier plugin.py avec le nouveau ou se positionner dans le répertoire domoticz directory/plugins et exécuter la commande suivante:
```
git pull
```

Donner la permission d'éxécution pour Linux:
```
chmod ugo+x plugin.py
```

Redémarrer Domoticz.

### Configuration

Ajouter le matériel Suez dans Domoticz au moyen du menu Configuration / Matériel, renseigner l'adresse e-mail et le mot de passe de votre compte toutsurmoneau. 

Vous pouvez choisir le nombre de jours d'historique à récupérer, avec le champ "jours", quelque chose comme **5** est l'idéal. 

Vous pouvez juste mettre une fois plus de jours pour récupérer de l'historique et remettre ensuite un nombre plus bas. Mercide noter que, lors de mes tests, je n'ai pu récupérer plus de 800 jours d'historique. Si vous avez des problèmes, merci de mettre un nombre de jour plus bas.

Après activation du matériel, vous avez un nouveau dispositif de mesures qui suit votre consommation avec un bouton Log.

### Migration depuis le plugin Markourai
***Merci de vous assurez que vous avez effectué une sauvegarde de votre base de données.***
Stop Domoticz et 
* Soit supprimer le répertoire  plugins/DomoticzSuez et réinstaller comme ci-dessus,
* Soit, si vous aviez utilisé git et exécuter les commandes suivantes:
```
git remote set-url origin https://github.com/yed30/DomoticzSuez
git pull

```
Redémarrer Domoticz.

Vous pouvez modifier le champ "jours", c'est à dire le nombre de jours à collecter pour récupérer l'historique.

## Authors
* Yed30 - 


## License

This project is licensed under the GPLv3 license - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
* **Mar Kourai** - [DomoticzSuez](https://github.com/Markourai/DomoticzSuez): Previous DomoticzSuez plugin
* inspired by [pyOdivea](https://github.com/fgrandouiller/pyOdivea) from **fgrandouiller**
* Domoticz team
 
