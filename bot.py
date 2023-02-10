import config
import telebot
import threading
import subprocess

from telebot import apihelper
apihelper.API_URL = "http://localhost:8080/bot{0}/{1}"

bot = telebot.TeleBot(config.token)
path = config.data_path
alert_timer = int(config.timer)
admin_id = None
chatId = None
alert = None

@bot.message_handler(commands=["on"])
def alertsOn(message):
    if message.from_user.id == config.admin_id:
        global alert
        alert = True
        bot.send_message(message.chat.id, 'Alerts ready to work')
        chatId = message.chat.id

        def used_disk_alert():
            if alert == True:
                threading.Timer(alert_timer, used_disk_alert).start()

                used_disk = subprocess.getoutput(["df -h | head -n 4 | grep " + path + " | awk '{print $5}' | tr -d '%'"])
                used_disk = int(used_disk)

                if (used_disk > 75) and (used_disk < 80):
                    bot.send_message(chatId, 'ALARM: Disk usage > 75% | Now used  ' + str(used_disk) + '%')

                if used_disk > 81:
                    bot.send_message(chatId, 'Disk Alert >81: ' + str(used_disk) + '%')

        used_disk_alert()

        def cpu_alert():
            if alert == True:
            	threading.Timer(alert_timer, cpu_alert).start()

            cpu_util = subprocess.getoutput(["top -b -n1 | grep 'load average' | awk '{print $12}' | tr -d ','"])
 #           cpu_util = float(cpu_util) fix cpu util
            if float(cpu_util) > float(0.05):
                bot.send_message(chatId, 'ALARM: high LA on server:  ' + str(cpu_util))
            #logic

        cpu_alert()

        def sync_alert():
            if alert == True:
            	threading.Timer(alert_timer, sync_alert).start()

            sync_speed = subprocess.getoutput(["journalctl -e -u subspaced.service  --since '1 minute ago' | tail -n1 | grep Syncing | awk '{print $11}'"])

            if float(sync_speed) < 0.1:
                bot.send_message(chatId, 'ALARM: node not sync now | Now sync speed is ' + str(sync_speed) +'bps')
        sync_alert()

@bot.message_handler(commands=["off"])
def alertsOff(message):
    if message.from_user.id == config.admin_id:
        global alert
        alert = False
        if alert == False:
            bot.send_message(message.chat.id, 'Alerts OFF')

@bot.message_handler(commands=["help"])
def help(message):
    if message.from_user.id == config.admin_id:
        bot.send_message(message.chat.id,
                    'Available commands: \n'
                    '0) /cpu - show cpu used \n'
                    '1) /disk - show actual FS usage \n'
                    '2) /ram - show actual RAM usage \n'
                    '3) /sync - show sync-progression \n'
                    '4) /brestart - restart tele-bot \n'
                    '5) /on - enable all alerts \n'
                    '6) /off - disable all alerts \n'
                         )

@bot.message_handler(commands=["disk"])
def disk(message):
    if message.from_user.id == config.admin_id:
        last_disk = subprocess.getoutput(["df -h /root/.local/share/subspace-cli/plots"])
        bot.send_message(message.chat.id, 'DISK: \n' + last_disk)

@bot.message_handler(commands=["brestart"])
def restart(message):
    if message.from_user.id == config.admin_id:
        bot.send_message(message.chat.id, 'BOT was restarted')
        restart = subprocess.run('systemctl restart telegram-bot.service', shell=True)

@bot.message_handler(commands=["ram"])
def ram(message):
    if message.from_user.id == config.admin_id:
        free_ram = subprocess.getoutput(["free -h | head -2 | awk '{print $2," "$3," "$4}'"])
        bot.send_message(message.chat.id, 'free RAM: \n' + free_ram)

@bot.message_handler(commands=["cpu"])
def cpu(message):
    if message.from_user.id == config.admin_id:
        free_cpu = subprocess.getoutput(["top -b -n1 | grep 'PID' -A3 | awk '{print $9,"   "$12}'"]) #top -b -n1 | grep 'PID' -A3 | awk '{print $9,"-->"$12}'
        bot.send_message(message.chat.id, 'TOP process list: \n\n' + free_cpu)

@bot.message_handler(commands=["sync"])
def sync(message):
    if message.from_user.id == config.admin_id:
        sync_state = subprocess.getoutput(["journalctl -u subspaced -xe | tail -n 1 | awk '/best/ {print $10,$11,$12,$13,$14,$15,$16,$17,$22,$23,$24,$25}'"])
        bot.send_message(message.chat.id, 'last sync log: \n' + sync_state)

@bot.message_handler(commands=["status"])
def status(message):
    if message.from_user.id == config.admin_id:
        bot.send_message(message.chat.id, 'main HW stats: \n' + cpu.free_cpu())

if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
