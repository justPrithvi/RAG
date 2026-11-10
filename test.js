var productExceptSelf = function(nums) {
    let left = 0
    let right = nums.length-1
    let maxWater = 0
    while(left < right) {
        let currMax = Math.min(nums[left], nums[right]) * (right-left)
        maxWater = Math.max(maxWater, currMax)
        nums[left] < nums[right] ? left+=1:right-=1
        
    }
    return maxWater
};

console.log(productExceptSelf([1,8,6,2,5,4,8,3,7]))