// Creates a pie chart for expenses by category
function createExpenseChart(labels, values) {
    const chartElement = document.getElementById("expenseChart");

    // Stop if chart element does not exist on this page
    if (!chartElement) {
        return;
    }

    new Chart(chartElement, {
        type: "pie",
        data: {
            labels: labels,
            datasets: [{
                label: "Expenses by Category",
                data: values
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// Creates a bar chart for monthly expenses
function createMonthlyChart(labels, values) {
    const chartElement = document.getElementById("monthlyChart");

    // Stop if chart element does not exist on this page
    if (!chartElement) {
        return;
    }

    new Chart(chartElement, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Monthly Expenses",
                data: values
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}
