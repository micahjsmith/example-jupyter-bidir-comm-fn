from threading import Event
from textwrap import dedent
from IPython.core.magics.display import Javascript
from IPython.display import display_javascript

class DescriptionStore:
    TIMEOUT = 20

    def __init__(self):
        self.description = ""
        self.event = Event()

    def before_prompt(self):
        """
        Preparing to issue the prompt by clearing the description flag.
        """
        self.event.clear() # flag is false
        self.description = ""

    def set_description(self, description):
        """
        Set the description and set the description flag.
        """
        self.description = description
        self.event.set() # flag is true, waiters notified
        print("[set_description] description set to {}".format(description))

    def get_description(self, timeout=None):
        """
        Wait for the description to be available, then return it.
        """
        if not timeout:
            timeout = self.TIMEOUT

        # wait returns True *unless* it times out.
        not_timed_out = self.event.wait(timeout=timeout) # wake

        if not not_timed_out:
            print("Timed out waiting for set_description event.")

        return self.description

class A:
    def __init__(self):
        self.description_store = DescriptionStore()

    def prompt_user(self):
        self.description_store.before_prompt()

        prompt_description_js = dedent("""\
        // Guard against re-execution.
        if (IPython.notebook.kernel) {
            console.log("beginning of js");
            var handle_output = function(out){
                console.log(out.msg_type);
                console.log(out);

                var res = null;
                if (out.msg_type == "stream"){
                    res = out.content.text;
                }
                // if output is a python object
                else if(out.msg_type === "execute_result"){
                    res = out.content.data["text/plain"];
                }
                // if output is a python error
                else if(out.msg_type == "error"){
                    res = out.content.ename + ": " + out.content.evalue;
                }
                // if output is something we haven't thought of
                else{
                    res = "[out type not implemented]";  
                }
                console.log(res);
            };
            var callback = {
                iopub: {
                    output : handle_output,
                }
            };
            var options = {
                silent : false,
            };

            var description = prompt("Set description", "default");
            var command = "a.description_store.set_description('" + description + "')";
            console.log("executing " + command);
            var kernel = IPython.notebook.kernel
            kernel.execute(command, callback, options);

            console.log("end of js");
        }
        """)
        jso = Javascript(prompt_description_js)
        display_javascript(jso)

        description = self.description_store.get_description()
        print("Description: {}".format(description))
        return description

a = A()
