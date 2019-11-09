# Serverless Nabaztag

This is a minimum implementation of an integration providing a media player for Serverless Nabaztag.

### Installation

Copy this folder to `<config_dir>/custom_components/nabaztag/`.

Add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
media_player:
  platform: nabaztag
  host: YOUR_NABAZTAG_IP_ADDRESS
```

### Acknowledgement

https://github.com/pantomax/Home-AssistantConfig/blob/master/packages/nabaztag.yaml
https://github.com/custom-components/media_player.braviatv_psk/tree/master/custom_components/braviatv_psk
https://github.com/home-assistant/example-custom-config/blob/master/custom_components/example_sensor/sensor.py
