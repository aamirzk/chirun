var opts = {
	lines: 13 // The number of lines to draw
	, length: 28 // The length of each line
	, width: 14 // The line thickness
	, radius: 42 // The radius of the inner circle
	, scale: 0.15 // Scales overall size of the spinner
	, corners: 1 // Corner roundness (0..1)
	, color: '#000' // #rgb or #rrggbb or array of colors
	, opacity: 0.25 // Opacity of the lines
	, rotate: 0 // The rotation offset
	, direction: 1 // 1: clockwise, -1: counterclockwise
	, speed: 1 // Rounds per second
	, trail: 60 // Afterglow percentage
	, fps: 20 // Frames per second when using setTimeout() as a fallback for CSS
	, zIndex: 2e9 // The z-index (defaults to 2000000000)
	, className: 'spinner' // The CSS class to assign to the spinner
	, top: '-24px' // Top position relative to parent
	, left: '97%' // Left position relative to parent
	, shadow: false // Whether to render a shadow
	, hwaccel: false // Whether to use hardware acceleration
	, position: 'relative' // Element positioning
}
var spinner = new Spinner(opts);
var codeMirrorInstances = {};
var runnerURL = "https://www.mas.ncl.ac.uk/coderunner";

function waitForSubmission(submissionid,codeBlock){
	setTimeout(function(){
		if(submissionid===undefined){
			return;
		}
		console.log("Checking the status of submission "+submissionid);
		$.post(runnerURL, {"@action": "check", "submissionid": submissionid}, null, "json")
			.done(function(data){
				if("status" in data && data['status'] == "waiting"){
					waitForSubmission(submissionid,codeBlock);
				}else if(data['result'] == "timeout"){
					console.log("Your job took too long to run");
				}else if(data['result'] == "overflow"){
					console.log('Your job used too much RAM');    
				}else if(data['result'] == "killed"){
					console.log("Your job was killed");
				} else {
					console.log(JSON.stringify(data));
					codeBlock.prev().removeAttr("disabled").removeAttr('style');
					codeBlock.append("<pre class='ran'><code class='sourceCode'>"+data['stdout']+data['stderr']+"</code></pre>");
					$('div.spinner').remove();
					if (typeof(Reveal) != "undefined"){
						Reveal.layout();
					}
				}
			})
			.fail(function(){
				console.log("A network error occured");
			});
	}, 1000);
}

function recieveRunnerConfirm(codeBlock){
	return function(msg){ 
		console.log("Got confirmation of message receipt:"+JSON.stringify(msg));
		waitForSubmission(msg["submissionid"],codeBlock);
	}
}

$( document ).ready(function() {
	$("pre.cm-block[data-runnable='true']").before('<button class="run-code">Run Code »</button>');

	$('pre.cm-block').each(function(){
		if (typeof(Reveal) != "undefined"){
			Reveal.layout();
		} else {
			var codeTag = $(this).find("code")[0];
			var codeMirrorOpts = {value: $(this).find("code").text()};
			codeMirrorOpts["lineNumbers"] = true;
			codeMirrorOpts["mode"] = $(this).data('language');
			var theCodeMirror = CodeMirror(function(elt) {
				codeTag.parentNode.replaceChild(elt, codeTag);
			} ,codeMirrorOpts);
			codeMirrorInstances[$(this).data('uuid')] = theCodeMirror;
		}
	});

	$('pre.cm-block').on('keydown',function(e){
		$(this).find('pre.ran').remove();
	});

	$('button.run-code').click(function(e){
		$(this).attr("disabled","disabled").css("background-color","#eeeeee").css("color","#111111");
		var codeBlock = $(this).next();
		var codeUUID = codeBlock.data('uuid');
		var codeLang = codeBlock.data('language');
		codeBlock.find('pre.ran').remove();
		codeBlock.append(spinner.spin().el)
		data = {"@action":"getCodeOutput",
			"codetype":codeLang+"_getoutput",
			"codeSource":codeMirrorInstances[codeUUID].getValue()
		};
		console.log("Sending message to Inginious:"+JSON.stringify(data));
		$.post(runnerURL,data,recieveRunnerConfirm(codeBlock));
	});
});
