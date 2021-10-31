# wireguard-ui

A web user interface to manage your WireGuard setup.

## Features
- Friendly UI
- Authentication
- Manage extra client's information (name, email, etc)
- Retrieve configs using QR code / file

## Run WireGuard-UI

Default username and password are `admin`.

### Using docker compose

You can take a look at this example of [docker-compose.yml](https://github.com/cyr-ius/wireguard-ui/blob/master/docker-compose.yaml). Please adjust volume mount points to work with your setup. Then run it like below:

```
docker-compose up
```

Note:

There is a Status option that needs docker to be able to access the network of the host in order to read the 
wireguard interface stats. See the `cap_add` and `network_mode` options on the docker-compose.yaml


### Environment Variables


Set the `SESSION_SECRET` environment variable to a random value.

In order to sent the wireguard configuration to clients via email (using sendgrid api) set the following environment variables

```
USERNAME: your root account
PASSWORD: your password account
USER_MAIL: root's mail
WIREGUARD_STARTUP:[True|False] Start wireguard at startup container
SECURITY_TWO_FACTOR: [True|False] Enable Totp panel
SECURITY_CHANGEABLE:[True|False] Enable Change passdword panel
SECURITY_PASSWORD_LENGTH_MIN: Length password
SECURITY_RECOVERABLE:[True|False] Enable recoverable account (send mail)
SECURITY_REGISTERABLE:[True|False] Accept register account at login page (Strongly discouraged )
SECURITY_CONFIRMABLE:[True|False] Confirm account A valid email address is required for root account
```


## License
MIT. See [LICENSE](https://github.com/cyr-ius/wireguard-ui/blob/master/LICENSE).