(function() {
    const selector = '__PLACEHOLDER_SELECTOR__';
    const delay = __PLACEHOLDER_DELAY__;

    function focusAndSelectElement(selector) {

        const nodeList = document.querySelectorAll(selector);
        const allElements = Array.from(nodeList);

        let element = null;
        let maxArea = -1;

        allElements.forEach(eachElement => {
            const width = eachElement.offsetWidth || 0;
            const height = eachElement.offsetHeight || 0;
            const area = width * height;

            if (area > maxArea) {
                maxArea = area;
                element = eachElement;
            }
        });

        if (element) {
            const eventOptions = { bubbles: true, cancelable: true, view: window };

            element.dispatchEvent(new MouseEvent('mousedown', eventOptions));
            element.focus();
            element.dispatchEvent(new MouseEvent('mouseup', eventOptions));
            element.click();

            // if (document.activeElement === element) {
            //     console.log("Focus Status: Success");
            // } else {
            //     console.log("Focus Status: Failed");
            // }
        }

        return element;
    }

    setTimeout(function() {
        focusAndSelectElement(selector);
    }, delay);
})();