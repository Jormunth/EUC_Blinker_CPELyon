Traceback (most recent call last):
  File "src/dbus_fast/message_bus.py", line 805, in dbus_fast.message_bus.BaseMessageBus._process_message
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/venv_euc_blinker/lib/python3.10/site-packages/bleak/backends/bluezdbus/manager.py", line 1026, in _parse_msg
    watcher.on_characteristic_value_changed(
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/venv_euc_blinker/lib/python3.10/site-packages/bleak/backends/bluezdbus/client.py", line 182, in on_value_changed
    callback(bytearray(value))
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/S6_G6_Deleule_Delzenne-Zamparutti/TOF_BLE_GUI (2).py", line 72, in handle_notification
    archive_data(data)
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/S6_G6_Deleule_Delzenne-Zamparutti/TOF_BLE_GUI (2).py", line 123, in archive_data
    json.dump(archive, file, indent=4)  # Sauvegarde avec indentation pour lisibilité
  File "/usr/lib/python3.10/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/usr/lib/python3.10/json/encoder.py", line 429, in _iterencode
    yield from _iterencode_list(o, _current_indent_level)
  File "/usr/lib/python3.10/json/encoder.py", line 325, in _iterencode_list
    yield from chunks
  File "/usr/lib/python3.10/json/encoder.py", line 405, in _iterencode_dict
    yield from chunks
  File "/usr/lib/python3.10/json/encoder.py", line 438, in _iterencode
    o = _default(o)
  File "/usr/lib/python3.10/json/encoder.py", line 179, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type bytearray is not JSON serializable
Données reçues : 1032.7148,-41.0156,-61.2793,-1.1450,2.4122,-0.1069
ERROR:root:A message handler raised an exception: Object of type bytearray is not JSON serializable
Traceback (most recent call last):
  File "/usr/lib/python3.10/asyncio/runners.py", line 44, in run
    return loop.run_until_complete(main)
  File "/usr/lib/python3.10/asyncio/base_events.py", line 636, in run_until_complete
    self.run_forever()
  File "/usr/lib/python3.10/asyncio/base_events.py", line 603, in run_forever
    self._run_once()
  File "/usr/lib/python3.10/asyncio/base_events.py", line 1871, in _run_once
    event_list = self._selector.select(timeout)
  File "/usr/lib/python3.10/selectors.py", line 469, in select
    fd_event_list = self._selector.poll(timeout, max_ev)
KeyboardInterrupt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "src/dbus_fast/message_bus.py", line 805, in dbus_fast.message_bus.BaseMessageBus._process_message
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/venv_euc_blinker/lib/python3.10/site-packages/bleak/backends/bluezdbus/manager.py", line 1026, in _parse_msg
    watcher.on_characteristic_value_changed(
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/venv_euc_blinker/lib/python3.10/site-packages/bleak/backends/bluezdbus/client.py", line 182, in on_value_changed
    callback(bytearray(value))
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/S6_G6_Deleule_Delzenne-Zamparutti/TOF_BLE_GUI (2).py", line 72, in handle_notification
    archive_data(data)
  File "/home/alix-deleule/Documents/CPE/5A/projet_majeur/S6_G6_Deleule_Delzenne-Zamparutti/TOF_BLE_GUI (2).py", line 123, in archive_data
    json.dump(archive, file, indent=4)  # Sauvegarde avec indentation pour lisibilité
  File "/usr/lib/python3.10/json/__init__.py", line 179, in dump
    for chunk in iterable:
  File "/usr/lib/python3.10/json/encoder.py", line 429, in _iterencode
    yield from _iterencode_list(o, _current_indent_level)
  File "/usr/lib/python3.10/json/encoder.py", line 325, in _iterencode_list
    yield from chunks
  File "/usr/lib/python3.10/json/encoder.py", line 405, in _iterencode_dict
    yield from chunks
  File "/usr/lib/python3.10/json/encoder.py", line 438, in _iterencode
    o = _default(o)
  File "/usr/lib/python3.10/json/encoder.py", line 179, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type bytearray is not JSON serializable
Données reçues : 1035.4004,-39.7949,-59.8145,-1.1832,2.6870,-0.0458
ERROR:root:A message handler raised an exception: Object of type bytearray is not JSON serializable
Traceback (most recent call last):
  File "/usr/lib/python3.10/asyncio/runners.py", line 44, in run
    return loop.run_until_complete(main)
  File "/usr/lib/python3.10/asyncio/base_events.py", line 636, in run_until_complete
    self.run_forever()
  File "/usr/lib/python3.10/asyncio/base_events.py", line 603, in run_forever
    self._run_once()
  File "/usr/lib/python3.10/asyncio/base_events.py", line 1871, in _run_once
    event_list = self._selector.select(timeout)
  File "/usr/lib/python3.10/selectors.py", line 469, in select
    fd_event_list = self._selector.poll(timeout, max_ev)
KeyboardInterrupt