// api.js
export async function fetchData(url, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${url}?${queryString}`);
    
    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }
    
    return await response.json();
}