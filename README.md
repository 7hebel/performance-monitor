# Performance Monitor

Computer's performance monitoring app similar to the Window's Task Manager. 

<img src="./assets/app.png" alt="App" />


### Monitors.

The monitors are defined in the `./Backend/monitors/` directory by creating a class inhereting from the `modules.monitor.MonitorBase`.
It contains: `target_title`, `product_info`, `hex_color` and `components_register`.

The `components_register` is a list of `KeyValueComponent`/`ChartComponent` or `ComponentsRow`. This list sets the structure of components on the Frontend.
<img src="./assets/composition.png" alt="Composition" />

The order of imports in the `./Backend/monitors/__init__.py` sets the order on Frontend.

### Components.

A component can represent a Key-Value pair where key is name of observed asset (like `Processes`) or a chart.
Every component has it's own, unique identificator being set of the `categoryId` and `itemId`.
`KeyValueComponent`'s style can be changed by setting the `important_item`.
<img src="./assets/importantitem.png" alt="ImportantItem" />
By default, all components are displayed in their own row. To group a few components in a single row, wrap them in the `ComponentsRow` class.

##### Components - Getters.

Component's getter is a function that returns a asset's value (like number of processes or usage of CPU).
There are two types of getters:

* **`AsyncReportingValueGetter`** - Used for a changing values like usage of CPU. This getter creates new thread that will check the output of getting function and if the value has changed, it **reports update** to the `state.UPDATES_BUFFER`. The getting function is called only if the output is needed - it's either displayed on the current page or it is a chart that needs constant updates.
Another thread (`modules.connection.updates_sender`) is checking every second for new reports in the `state.UPDATES_BUFFER`. If any changes has been reported, it packs them and sends to the Frontend WS client in single message. 

* **`StaticValueGetter`** - Used for a constant values. Value of this getter is included in the initial composition message.

    - *`lazy_static_getter`* - If obtaining an constant information takes too long, using this getter is recomended. Creates StaticValueGetter with a placeholder value, starts background evaluation job and immediately returns a blank getter, so the startup can continue without waiting for this value. When desired value is calculated in the background process, it reports itself to the `UPDATES_BUFFER` and the change is sent in the next updates packet. The value is also assigned to the previously created blank getter, so in case of Frontend's reconnection it doesn't have to be reevaluated.

