
# GSIP 169 - QoS WMS GetCapabilities Extension

## Overview

Allow GeoServer extends WMS GetCapabilities with optional QoS elements.

### Proposed By

Fernando Miño

### Assigned to Release

This proposal is for GeoServer 2.14-beta.

### State

* [X] Under Discussion
* [ ] In Progress
* [ ] Completed
* [ ] Rejected
* [ ] Deferred

### Motivation

The QoSE DWG has been discussing over the last year a number of extensions to standard GetCapabilities documents for various OGC services in order to enable and guide automatic QoS testing for OGC services endpoints while retaining the ability to safely ignore such extension for non QoS oriented clients.

Such extensions would cover the following:
* Operating Info
    * Operational status (test/demo/beta/production etc.)
    * Operating days & hours (default: 24/7)
* Scheduled maintenance
    * Regular maintenance windows, upcoming planned downtime events
* QoS statements applying to the entire service
    * Metrics & minimum values to be expected, availability, capacity etc.
* Representative operations
    * QoS statements for given operations & limited request parameters
    * Intended use cases: auto-configuration for QoS monitoring tools, automatic cataloguing, generating relevant preview data for client software etc

[QoS xml examples](https://github.com/opengeospatial/QoSE-DWG/tree/master/QoSMetadata)

## Proposal

### WMS 1.3.0 and WFS 2.0.1 Services QoS Metadata Extensions

#### GetCapabilities QoS Plugin extension point interface

QosWMSCapabilitiesProvider and QosWFSCapabilitiesProvider interfaces would allow any plugin to inject QoS XML metadata into <qos-wms:QualityOfServiceMetadata> & <qos-wfs:QualityOfServiceMetadata> extended tag.
Plugins would register a spring-bean that implements this interface with its encode function.

<qos-wms:QualityOfServiceMetadata> and <qos-wfs:QualityOfServiceMetadata> extended tags and its internal metadata tags will be located in standard substitution place of _ExtendedCapabilities.

Main and service agnostic interface:

```java
package org.geoserver;

import java.io.IOException;

import org.geoserver.ExtendedCapabilitiesProvider.Translator;
import org.geoserver.config.ServiceInfo;

/**
 * Extension point that allows plugins to dynamically contribute extended properties to the QoS
 * capabilities Root tag in GetCapabilities request.
 *
 * @param <Info>
 * @param <Request>
 */
public interface QosCapabilitiesProvider<Info extends ServiceInfo, Request> {
    
    /**
     * Encodes the extended capabilities.
     *
     * @param tx the translator used to encode the extended capabilities to
     * @param serviceInfo service metadata
     * @param request the originating request, may be useful for the provider to decide whether or
     *     not, or how, to contribute to the capabilities document
     */
    void encode(Translator tx, Info serviceInfo, Request request) throws IOException;
    
}
```

QoS WMS GetCapabilities extension point:

```java
package org.geoserver.wms;

import java.io.IOException;

import org.geoserver.ExtendedCapabilitiesProvider.Translator;
import org.geoserver.QosCapabilitiesProvider;

/**
 * QoS WMS GetCapabilities extension point
 */
public interface QosWMSCapabilitiesProvider 
    extends QosCapabilitiesProvider<WMSInfo, GetCapabilitiesRequest> {
    
    void encode(Translator tx, WMSInfo wfs, GetCapabilitiesRequest request) throws IOException;
    
}
```

QoS WFS GetCapabilities extension point:

```java
package org.geoserver.wfs;

import org.geoserver.QosCapabilitiesProvider;
import org.geoserver.wfs.WFSInfo;
import org.geoserver.wfs.request.GetCapabilitiesRequest;

/**
 * QoS WFS extension point
 *
 */
public interface QosWFSCapabilitiesProvider extends 
    QosCapabilitiesProvider<WFSInfo, GetCapabilitiesRequest> {
    
    void encode(Translator tx, WFSInfo serviceInfo, GetCapabilitiesRequest request) throws IOException;
    
}
```

#### QoS Extension bean example:

Creating bean class in "opinfo" plugin for WMS:

```java
    public class OperatingInfoQosMetadata implements QosWMSCapabilitiesProvider {
        ...
    }
```

Spring ApplicationContext bean definition:

```xml
    <bean id="operatingInfoQosMetadata" class="org.geoserver.opinfo.wms.OperatingInfoQosMetadata">
    </bean>
```

Creating bean class in "opinfo" plugin for WFS:

```java
    public class WFSOperatingInfoQosMetadata implements QosWFSCapabilitiesProvider {
        ...
    }
```

Spring ApplicationContext bean definition:

```xml
    <bean id="wfsOperatingInfoQosMetadata" class="org.geoserver.opinfo.wfs.WFSOperatingInfoQosMetadata">
    </bean>
```

QoS OperatingInfo XML metadata encoded:

```xml
<qos-wms:QualityOfServiceMetadata>
...
    <qos:OperatingInfo>
        <qos:OperationalStatus xlink:href="http://def.opengeospatial.org/codelist/qos/status/1.0/operationalStatus.rdf#Operational" xlink:title="Operational" />
        <qos:ByDaysOfWeek>
            <qos:On>Monday Tuesday Wednesday Thursday Friday</qos:On>
            <qos:StartTime>06:00:00+03:00</qos:StartTime>
            <qos:EndTime>17:59:59+03:00</qos:EndTime>
        </qos:ByDaysOfWeek>
        <qos:ByDaysOfWeek>
            <qos:On>Saturday</qos:On>
            <qos:StartTime>10:00:00+03:00</qos:StartTime>
            <qos:EndTime>14:59:59+03:00</qos:EndTime>
        </qos:ByDaysOfWeek>
    </qos:OperatingInfo>
...
</qos-wms:QualityOfServiceMetadata>
```


#### Internal handling

Internally, each WMS and WFS geoserver modules will instance(register) a default QosRootWM*CapabilitiesProvider spring-bean.

Since this bean extends ExtendedCapabilitiesProvider/WFSExtendedCapabilitiesProvider, it always will be located by WMS/WFS GetCapabilities extensions loader and executed. Then it will load its own QoSCapabilities extensions, iterate over them and encode their XML metadata into response, inside <qos-w*s:QualityOfServiceMetadata>

QosRootWMSCapabilitiesProvider/QosRootWFSCapabilitiesProvider bean would check if at least one Qos metadata provider is loaded for to print its root tag and schemas location into GetCapabilities response.

Internal ExtendedCapabilitiesProvider default bean for WMS:

```java

public class QosRootWMSCapabilitiesProvider implements ExtendedCapabilitiesProvider {
    ...
```

Spring ApplicationContext bean definition:

```xml
    <bean id="qosRootWMSCapabilitiesProvider" class="org.geoserver.wms.QosRootWMSCapabilitiesProvider">
    </bean>
```

Internal ExtendedCapabilitiesProvider default bean for WFS:

```java

public class QosRootWFSCapabilitiesProvider implements WFSExtendedCapabilitiesProvider
    ...
```

Spring ApplicationContext bean definition:

```xml
    <bean id="qosRootWFSCapabilitiesProvider" class="org.geoserver.wfs.QosRootWFSCapabilitiesProvider">
    </bean>
```




