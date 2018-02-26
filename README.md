# signalfx-to-statuspage
_signalfx-to-statuspage_ is a simple Lambda function that allows you to publish a SignalFx chart to your StatusPage.io 
public metrics using a SignalFlow program. 

More information on how you can publish SignalFx metrics to StatusPage.io using SignalFlow can be found on our [Blog](https://medium.com/poka-techblog/integrate-signalfx-with-statuspage-io-effortlessly-using-signalflow-6118d878c703).

## Requirements
 * The _AWS CLI_ installed and configured.
 * Python 3


## Installation
1. First clone this repository.

2. Copy the template file `config.ini.template` to `config.ini` and edit it using the appropriate values.
  
    **SignalFxApiKey**: _Can be found in the administrative page under the "Access Tokens" section in SignalFX_
    
    **SignalFxSignalFlowProgramBase64**: _The SignalFlow program encoded in base64 that will be executed to extract the datapoints from SignalFx_
    
    **StatusPageApiKey**: _Can be found in the API tab of the "Manage Account" page in StatusPage_
    
    **StatusPageMetricId**: _Unique ID for your organization in StatusPage.io_
    
    **StatusPagePageId**: _Can be found in the advanced options of this metric on StatusPage_

3. Run `make deploy` and you're done!

    A. Optionally, you can customize the target bucket for the Lambda code. `make deploy BUCKET_NAME=my-lambda-bucket`
    
    B. You can also customize the CloudFormation stack name. `make deploy STACK_NAME=my-metric-system-integration`
    

### Limitations
 * The SignalFlow program must be less than 4Kb once encoded in Base64


### Future improvements
 * Tests 
 * Automatically pull the SignalFlow code from SignalFx
 * Create the public metric in StatusPage if it doesn't exist
 
