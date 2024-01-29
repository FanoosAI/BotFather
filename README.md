# Bot Father

You wanna publish a public bot? You need to talk to the BotFather!

## How to use
Just send him a respectful message, and he will register your bot to be available after it's been verified by the admin.

## How to run
This bot is run via OPSDroid. 
Make sure you have the right packages installed. run:
```shell
pip install opsdroid opsdroid[all]
pip install matrix-nio[e2e]
```
in addition to the requirements in the requirements.txt file. (the OLM encryption library can be a pain!)

Don't forget to 
1- setup the configuration.yaml file and set the proper username and password for bots and database
2- provide the api_key in api_key.yaml file in the root directory

Then you can run it with `opsdroid start`
