## Ingress Adapter iKontrol

### Usage
This chart comes unconfigured and will need to be configured with the following values to work.

Undefined values:  
```image.repository```  
```image.tag```

There are some undefined values ```inside the config.conf.ini```
The undefined values are:
* ```ingress_url ```
* ```source```
* ```api_url```
* ```api_version```

### Credentials
The helm chart pulls some secrets from the hashicorp vault.  
The name used to get the secret is based on the appName.  
[How it's done](https://github.com/Open-Dataplatform/ingress-adapter-ikontrol/blob/f2b27be37ce2fdebbe7f0461b1e2087e688c4d61/chart/templates/adapter-wf-tp.yaml#L31-L46)

[Vault annotations](https://www.vaultproject.io/docs/platform/k8s/injector/annotations)

### Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `appName` | The overall name | ingress-adapter-ikontrol
| `image.repository` | The repository of the image | nil
| `image.tag` | The tag of the image | latest
| `schedule` | Cron schedule | "0 1 * * *"
| `transformationparams.datestring` | The ingestion time / start time | empty string
| `config.'conf.ini'` | Config for the app | see [here](https://github.com/Open-Dataplatform/ingress-adapter-ikontrol/#configuration)
| `config.'log.conf'` | Logging config for the app | see [here](https://github.com/Open-Dataplatform/ingress-adapter-ikontrol/#configuration)
