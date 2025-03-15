from intergrations import dynatrace
from modules import identificators
from modules import metrics
from modules import state

import unittest
import time


class TestIdentificators(unittest.TestCase):
    def test_structure(self) -> None:
        identificator = identificators.Identificator("testCategory", "testItem")
        self.assertEqual(identificator.full(), "testCategory.testItem", "Identificator changed format.")

    def test_parser(self) -> None:
        category = "category"
        item_id = "item"
        
        standard_identificator_str = f"{category}.{item_id}"
        parsed_standard_id = identificators.parse_identificator(standard_identificator_str)
        self.assertEqual(parsed_standard_id.category, category, "Parsed category not matching actual category.")
        self.assertEqual(parsed_standard_id.item_id, item_id, "Parsed itemId not matching actual itemId.")

        invalid_identificator_str = f"{category} {item_id}"  # Invalid ID - no separator (`.`)
        with self.assertRaises(ValueError):
            identificators.parse_identificator(invalid_identificator_str)


class TestMetricGetters(unittest.TestCase):
    def test_static_getter(self) -> None:
        for value in ("value", 18, 0.4):
            getter = metrics.StaticValueGetter(value)
            self.assertEqual(getter(), value, f"StaticValueGetter returned different value than passed: (set:`{value}`, got:{getter()})")

        getter = metrics.StaticValueGetter("-")
        getter.value = 24
        self.assertEqual(getter(), 24, "Manually set StaticValueGetter's value is not returned correctly.")

    def test_lazy_static_getter(self) -> None:
        lazy_value = 5
        def slow_value_getter():
            time.sleep(0.3)
            return lazy_value
        
        lazy_test_id = identificators.Identificator("test", "lazyTest")
        lazy_getter = metrics.lazy_static_getter(lazy_test_id, slow_value_getter)

        self.assertEqual(lazy_getter(), "-", "Not evaluated lazy_static_getter returned not-placeholder value.")
        time.sleep(0.4)
        self.assertEqual(lazy_getter(), lazy_value, f"lazy_static_getter should be evaluated correctly at this point but returned different value: {lazy_getter()}")
        self.assertIn(lazy_test_id.full(), state.UPDATES_BUFFER.updates, "lazy_static_getter evaluated correctly but didn't report change to the state.UPDATES_BUFFER")
        self.assertEqual(state.UPDATES_BUFFER.updates[lazy_test_id.full()], lazy_value, f"lazy_static_getter evaluated value correctly, but reported invalid value")

    def test_async_reporting_getter(self) -> None:
        dynatrace.ENABLE_LOGGING = False
        
        class _Counter:
            def __init__(self) -> None:
                self.last_result = 0
            
            def __call__(self) -> None:
                self.last_result += 1
                return self.last_result
            
        test_counter = _Counter()
        test_id = identificators.Identificator("test", "AsyncGetterTest")
        metrics.KeyValueMetric(
            identificator=test_id,
            title="test",
            getter=test_counter
        )
        
        time.sleep(0.15)
        self.assertIn(test_id.full(), state.UPDATES_BUFFER.updates, "AsyncReportingValueGetter didn't report initial value.")

        time.sleep(1)
        self.assertGreater(state.UPDATES_BUFFER.updates[test_id.full()], 1, "AsyncReportingValueGetter should have changed value since inital_report but didn't.")

    
class TestState(unittest.TestCase):
    def test_updates_buffer(self) -> None:
        buffer = state._ValueUpdatesBuffer()
        
        identificators_category = "bufferTest"
        id1 = identificators.Identificator(identificators_category, "1")
        id2 = identificators.Identificator(identificators_category, "2")
        
        buffer.insert_update(id1, 1)
        buffer.insert_update(id2, 2)
        buffer.insert_update(id2, 3)
        
        self.assertEqual(len(buffer.updates), 2, "Two buffer updates were not saved in the .updates")
        
        saved_state = buffer.flush()
        self.assertEqual(len(buffer.updates), 0, "Buffer was flushed, but some data remaining.")
        self.assertEqual(len(saved_state), 2, "Buffer was filled, but when flushed resulted in blank dict.")
        
        
    

if __name__ == '__main__':
    unittest.main()
