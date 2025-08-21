class TestClass {
    init(name: string) {
        this.name = name;
    }
    
    function getName(): string {
        return this.name;
    }
}

let obj: TestClass = new TestClass("test");
let result: string = obj.getName();
