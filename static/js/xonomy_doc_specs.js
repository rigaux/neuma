    	var xonomy_note_spec={
    			
    			elements: {
    			"note": {
    				hasText: false,
    				menu: [    			
    				       {
    				    	   caption: "Delete this <note>", action: Xonomy.deleteElement
    				       },
    				       {
    				    	   caption: "New <note> before this", action: Xonomy.newElementBefore, actionParameter: "<note/>"
    				       },
    				       {
    				    	   caption: "New <note> after this", action: Xonomy.newElementAfter, actionParameter: "<note/>"
    				       }
    				      ],
    			attributes: {
    				"pname": {asker: Xonomy.askPicklist, 
    					askerParameter: [
    					        {value: "a"},
    					        {value: "b"}, {value: "c"},{value: "d"}, {value: "e"}, {value: "f"},{value: "g"}]},
    				"oct": {asker: Xonomy.askPicklist,
    					askerParameter: [
    					        {value: "1"},
    					        {value: "2"}, {value: "3"},{value: "4"}, {value: "5"}, {value: "6"},{value: "7"}]},
    				"dur": {asker: Xonomy.askString},
    				"accid": {asker: Xonomy.askPicklist,
    					askerParameter: [
    					        {value: "s"}, {value: "f"}, {value: ""}]}
    				} 
    			}
    			} 
    		};
